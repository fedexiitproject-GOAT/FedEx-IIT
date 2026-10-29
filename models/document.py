import base64
import binascii
import os
from odoo import api, fields, models
from odoo.exceptions import ValidationError

DEFAULT_EXTENSIONS = "pdf,doc,docx,xls,xlsx,ppt,pptx,csv,txt,zip,png,jpg,jpeg,ipynb,py"


class FedexDocument(models.Model):
    _name = "fedex.document"
    _description = "FedEx Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "upload_date desc,id desc"

    name = fields.Char(required=True, default="New", index=True)
    doc_type_id = fields.Many2one("fedex.document.type", required=True, index=True, ondelete="restrict")
    project_id = fields.Many2one("fedex.project", index=True, ondelete="restrict")
    partner_id = fields.Many2one("res.partner", index=True, ondelete="restrict")
    member_id = fields.Many2one("fedex.project.member", index=True, ondelete="cascade")
    file = fields.Binary(attachment=True, required=True)
    filename = fields.Char(required=True)
    version = fields.Integer(default=1, required=True)
    active = fields.Boolean(default=True, index=True)
    uploaded_by = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    upload_date = fields.Datetime(default=fields.Datetime.now, readonly=True)

    @api.depends("name", "filename", "version")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s v%s" % (rec.name, rec.version)

    @api.onchange("file", "filename")
    def _onchange_filename(self):
        if self.filename and (not self.name or self.name == "New"):
            self.name = self.filename

    @api.model
    def _repository_config(self):
        params = self.env["ir.config_parameter"].sudo()
        return (
            float(params.get_param("fedex_repository.max_upload_mb", 25)),
            [x.strip().lower() for x in params.get_param("fedex_repository.allowed_extensions", DEFAULT_EXTENSIONS).split(",") if x.strip()],
        )

    def _validate_file(self, vals):
        filename = vals.get("filename") or self.filename
        data = vals.get("file")
        if not filename or not data:
            return
        extension = os.path.splitext(filename.lower())[1].lstrip(".")
        max_mb, allowed = self._repository_config()
        if extension not in allowed:
            raise ValidationError("File extension is not allowed. Allowed extensions: %s" % ", ".join(allowed))
        try:
            decoded = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValidationError("The uploaded file is not valid base64 data.") from exc
        if len(decoded) > max_mb * 1024 * 1024:
            raise ValidationError("The uploaded file exceeds the configured maximum size of %.2f MB." % max_mb)

    def _prepare_owner(self, vals):
        vals = dict(vals)
        dt = self.env["fedex.document.type"].browse(vals.get("doc_type_id"))
        if not dt.exists():
            raise ValidationError("A valid document type is required.")
        if dt.scope == "engagement":
            if not vals.get("member_id"):
                raise ValidationError("Engagement documents require a project member.")
            member = self.env["fedex.project.member"].browse(vals["member_id"]).exists()
            if not member:
                raise ValidationError("The selected project member does not exist.")
            vals.update(project_id=member.project_id.id, partner_id=member.partner_id.id)
            if dt.applies_to_person != "all":
                profile_map = {"student": member.partner_id.is_student, "faculty": member.partner_id.is_faculty, "staff": member.partner_id.is_staff}
                if not profile_map.get(dt.applies_to_person, False):
                    raise ValidationError("This document type does not apply to the selected person's profile.")
        if dt.scope == "person" and (not vals.get("partner_id") or vals.get("project_id") or vals.get("member_id")):
            raise ValidationError("Person documents require partner only.")
        if dt.scope == "project" and (not vals.get("project_id") or vals.get("partner_id") or vals.get("member_id")):
            raise ValidationError("Project documents require project only.")
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            self._validate_file(vals)
            vals = self._prepare_owner(vals)
            if vals.get("name") in (None, "New"):
                vals["name"] = vals.get("filename") or "Document"
            prepared.append(vals)
        records = super().create(prepared)
        self.env["fedex.document.requirement"]._sync_requirements(records)
        return records

    def write(self, vals):
        for rec in self:
            if any(key in vals for key in ("file", "filename", "doc_type_id", "project_id", "partner_id", "member_id")):
                merged = {"file": vals.get("file", rec.file), "filename": vals.get("filename", rec.filename), "doc_type_id": vals.get("doc_type_id", rec.doc_type_id.id), "project_id": vals.get("project_id", rec.project_id.id), "partner_id": vals.get("partner_id", rec.partner_id.id), "member_id": vals.get("member_id", rec.member_id.id)}
                self._validate_file(merged)
                self._prepare_owner(merged)
        result = super().write(vals)
        if set(vals) & {"active", "doc_type_id", "project_id", "partner_id", "member_id"}:
            self.env["fedex.document.requirement"]._sync_requirements(self)
        return result

    def action_replace(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": "Replace File", "res_model": "fedex.document.replace.wizard", "view_mode": "form", "target": "new", "context": {"default_document_id": self.id}}

    def action_download(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url", "url": f"/web/content/{self._name}/{self.id}/file/{self.filename}?download=true", "target": "self"}

    def action_preview(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url", "url": f"/web/content/{self._name}/{self.id}/file/{self.filename}", "target": "new"}


class FedexDocumentRequirement(models.Model):
    _name = "fedex.document.requirement"
    _description = "Document Requirement"
    _order = "active desc,doc_type_id,id"

    doc_type_id = fields.Many2one("fedex.document.type", required=True, ondelete="cascade", index=True)
    project_id = fields.Many2one("fedex.project", index=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner", index=True, ondelete="cascade")
    member_id = fields.Many2one("fedex.project.member", index=True, ondelete="cascade")
    document_id = fields.Many2one("fedex.document", index=True, ondelete="set null")
    state = fields.Selection([("missing", "Missing"), ("uploaded", "Uploaded")], compute="_compute_state", store=True, index=True)
    active = fields.Boolean(default=True, index=True)
    owner_key = fields.Char(required=True, index=True)

    _sql_constraints = [("owner_type_uniq", "unique(doc_type_id,owner_key)", "A document requirement already exists for this owner and type.")]

    @api.depends("doc_type_id", "owner_key", "state")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s" % (rec.doc_type_id.name, rec.owner_key)

    @api.depends("document_id", "document_id.active", "active")
    def _compute_state(self):
        for rec in self:
            rec.state = "uploaded" if rec.active and rec.document_id and rec.document_id.active else "missing"

    @api.constrains("doc_type_id", "project_id", "partner_id", "member_id")
    def _check_owner(self):
        for rec in self:
            scope = rec.doc_type_id.scope
            if scope == "person" and (not rec.partner_id or rec.project_id or rec.member_id):
                raise ValidationError("Person requirements must have partner only.")
            if scope == "project" and (not rec.project_id or rec.partner_id or rec.member_id):
                raise ValidationError("Project requirements must have project only.")
            if scope == "engagement" and (not rec.member_id or not rec.project_id or not rec.partner_id):
                raise ValidationError("Engagement requirements must have member, project and partner derived from the engagement.")

    @api.model
    def _sync_requirements(self, owners):
        if not owners:
            return True
        projects = self.env["fedex.project"].browse()
        members = self.env["fedex.project.member"].browse()
        partners = self.env["res.partner"].browse()
        owner_names = set()
        if getattr(owners, "_name", None) == "fedex.project":
            projects |= owners
            members |= owners.mapped("member_ids")
            partners |= members.mapped("partner_id")
            owner_names.add("project")
        elif getattr(owners, "_name", None) == "fedex.project.member":
            members |= owners
            projects |= owners.mapped("project_id")
            partners |= owners.mapped("partner_id")
            owner_names.add("member")
        elif getattr(owners, "_name", None) in ("fedex.student", "fedex.faculty", "fedex.staff"):
            partners |= owners.mapped("partner_id")
            owner_names.add("partner")
        elif getattr(owners, "_name", None) == "fedex.document":
            projects |= owners.mapped("project_id")
            members |= owners.mapped("member_id")
            partners |= owners.mapped("partner_id")
            owner_names.update({"project", "member", "partner"})
        elif getattr(owners, "_name", None) == "fedex.document.type":
            # Rule changes must be reflected immediately; the nightly cron remains the safety net.
            projects = self.env["fedex.project"].search([])
            members = self.env["fedex.project.member"].search([])
            partners = self.env["res.partner"].search([])
            owner_names.update({"project", "member", "partner"})
        else:
            return True

        desired = {}
        doc_types = self.env["fedex.document.type"].search([("active", "=", True), ("is_mandatory", "=", True)])
        for partner in partners:
            has_profiles = {
                "student": bool(self.env["fedex.student"].search_count([("partner_id", "=", partner.id), ("active", "=", True)])),
                "faculty": bool(self.env["fedex.faculty"].search_count([("partner_id", "=", partner.id), ("active", "=", True)])),
                "staff": bool(self.env["fedex.staff"].search_count([("partner_id", "=", partner.id), ("active", "=", True)])),
            }
            for dt in doc_types.filtered(lambda x: x.scope == "person"):
                if dt.applies_to_person == "all" or has_profiles.get(dt.applies_to_person):
                    desired[(dt.id, f"partner:{partner.id}")] = {"doc_type_id": dt.id, "partner_id": partner.id, "owner_key": f"partner:{partner.id}"}
        for project in projects:
            for dt in doc_types.filtered(lambda x: x.scope == "project"):
                if not dt.applies_to_type_ids or project.type_id in dt.applies_to_type_ids:
                    desired[(dt.id, f"project:{project.id}")] = {"doc_type_id": dt.id, "project_id": project.id, "owner_key": f"project:{project.id}"}
        for member in members:
            for dt in doc_types.filtered(lambda x: x.scope == "engagement"):
                if (not dt.applies_to_type_ids or member.project_id.type_id in dt.applies_to_type_ids):
                    profile_ok = dt.applies_to_person == "all" or {
                        "student": member.partner_id.is_student,
                        "faculty": member.partner_id.is_faculty,
                        "staff": member.partner_id.is_staff,
                    }.get(dt.applies_to_person, False)
                    if profile_ok:
                        desired[(dt.id, f"member:{member.id}")] = {"doc_type_id": dt.id, "member_id": member.id, "project_id": member.project_id.id, "partner_id": member.partner_id.id, "owner_key": f"member:{member.id}"}

        keys = list({key for _, key in desired}) or ["__none__"]
        current = self.search([("owner_key", "in", keys)])
        by_key = {(rec.doc_type_id.id, rec.owner_key): rec for rec in current}
        for key, vals in desired.items():
            rec = by_key.get(key)
            if rec:
                if not rec.active:
                    rec.active = True
            else:
                rec = self.create(vals)
            # Always bind the latest active version to the checklist.
            latest_domain = [("doc_type_id", "=", vals["doc_type_id"]), ("active", "=", True)]
            if vals.get("partner_id"):
                latest_domain.append(("partner_id", "=", vals["partner_id"]))
            if vals.get("project_id"):
                latest_domain.append(("project_id", "=", vals["project_id"]))
            if vals.get("member_id"):
                latest_domain.append(("member_id", "=", vals["member_id"]))
            latest = self.env["fedex.document"].search(latest_domain, order="upload_date desc,id desc", limit=1)
            if rec.document_id != latest:
                rec.document_id = latest.id or False
        desired_keys = set(desired)
        for rec in current:
            if (rec.doc_type_id.id, rec.owner_key) not in desired_keys:
                if rec.document_id:
                    rec.active = False
                else:
                    rec.unlink()
        return True

    def action_upload(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": "Upload Document", "res_model": "fedex.document", "view_mode": "form", "target": "new", "context": {"default_doc_type_id": self.doc_type_id.id, "default_project_id": self.project_id.id, "default_partner_id": self.partner_id.id, "default_member_id": self.member_id.id, "default_filename": self.doc_type_id.name}}
