from datetime import date
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FedexProject(models.Model):
    _name = "fedex.project"
    _description = "FedEx Project"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc"

    code = fields.Char(required=True, default="New", copy=False, index=True)
    name = fields.Char(required=True, index=True)
    description = fields.Html()
    centre_id = fields.Many2one("fedex.centre", required=True, index=True, ondelete="restrict")
    type_id = fields.Many2one("fedex.project.type", required=True, index=True, ondelete="restrict")
    category_ids = fields.Many2many("fedex.project.category", string="Categories")
    sponsor_id = fields.Many2one("fedex.sponsor", index=True, ondelete="restrict")
    supervisor_id = fields.Many2one("fedex.faculty", index=True, ondelete="restrict")
    state = fields.Selection([
        ("yet_to_start", "Yet to Start"), ("in_progress", "In Progress"), ("on_hold", "On Hold"),
        ("completed", "Completed"), ("cancelled", "Cancelled")], default="yet_to_start", required=True, tracking=True, index=True)
    priority = fields.Selection([("low", "Low"), ("normal", "Normal"), ("high", "High"), ("critical", "Critical")], default="normal", required=True, tracking=True)
    start_date = fields.Date()
    expected_end_date = fields.Date()
    actual_end_date = fields.Date()
    progress_manual = fields.Float(string="Manual Progress", default=0.0)
    progress = fields.Float(compute="_compute_progress", inverse="_inverse_progress", store=True)
    member_ids = fields.One2many("fedex.project.member", "project_id", string="Team")
    milestone_ids = fields.One2many("fedex.milestone", "project_id", string="Milestones")
    document_ids = fields.One2many("fedex.document", "project_id", string="Documents")
    requirement_ids = fields.One2many("fedex.document.requirement", "project_id", string="Requirements")
    member_count = fields.Integer(compute="_compute_stats", store=True)
    milestone_done_count = fields.Integer(compute="_compute_stats", store=True)
    milestone_count = fields.Integer(compute="_compute_stats", store=True)
    days_remaining = fields.Integer(compute="_compute_days", store=True)
    is_nearing_completion = fields.Boolean(compute="_compute_days", store=True, index=True)
    missing_doc_count = fields.Integer(compute="_compute_missing", store=True)
    is_internship = fields.Boolean(related="type_id.is_internship", store=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    active = fields.Boolean(default=True)

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s" % (rec.code, rec.name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code") in (None, "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("fedex.project") or "New"
            vals.setdefault("company_id", self.env.company.id)
        recs = super().create(vals_list)
        self.env["fedex.document.requirement"]._sync_requirements(recs)
        return recs

    def write(self, vals):
        old_type = self.mapped("type_id") if "type_id" in vals else self.env["fedex.project.type"]
        res = super().write(vals)
        if "type_id" in vals:
            self.env["fedex.document.requirement"]._sync_requirements(self)
        return res

    @api.depends("milestone_ids.done", "milestone_ids")
    def _compute_progress(self):
        for rec in self:
            if rec.milestone_ids:
                rec.progress = round(100.0 * len(rec.milestone_ids.filtered("done")) / len(rec.milestone_ids), 2)
            else:
                rec.progress = max(0.0, min(100.0, rec.progress_manual))

    def _inverse_progress(self):
        for rec in self:
            if not rec.milestone_ids:
                rec.progress_manual = max(0.0, min(100.0, rec.progress))

    @api.depends("member_ids", "milestone_ids", "milestone_ids.done")
    def _compute_stats(self):
        for rec in self:
            rec.member_count = len(rec.member_ids)
            rec.milestone_count = len(rec.milestone_ids)
            rec.milestone_done_count = len(rec.milestone_ids.filtered("done"))

    @api.depends("expected_end_date", "state")
    def _compute_days(self):
        threshold = int(self.env["fedex.repository.settings"]._get_param("nearing_days", 30))
        today = date.today()
        for rec in self:
            rec.days_remaining = (rec.expected_end_date - today).days if rec.expected_end_date else 0
            rec.is_nearing_completion = bool(rec.state == "in_progress" and rec.expected_end_date and 0 <= rec.days_remaining <= threshold)

    @api.depends("requirement_ids.state", "requirement_ids.active")
    def _compute_missing(self):
        for rec in self:
            rec.missing_doc_count = len(rec.requirement_ids.filtered(lambda r: r.active and r.state == "missing"))

    @api.constrains("code")
    def _check_code(self):
        for rec in self:
            if self.search_count([("code", "=", rec.code), ("id", "!=", rec.id)]):
                raise ValidationError("Project code must be unique.")

    @api.constrains("start_date", "expected_end_date", "actual_end_date", "state")
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.expected_end_date and rec.expected_end_date < rec.start_date:
                raise ValidationError("Expected end date cannot be before start date.")
            if rec.start_date and rec.actual_end_date and rec.actual_end_date < rec.start_date:
                raise ValidationError("Actual end date cannot be before start date.")
            if rec.state == "completed" and not rec.actual_end_date:
                raise ValidationError("Actual end date is required when a project is completed.")

    def action_mark_completed(self):
        self.write({"state": "completed", "actual_end_date": date.today()})
        return True

    def action_add_members(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": "Add Members", "res_model": "fedex.add.member.wizard", "view_mode": "form", "target": "new", "context": {"default_project_id": self.id}}

    @api.model
    def cron_recompute_dates(self):
        self.search([])._compute_days()
        return True

    @api.model
    def dashboard_data(self):
        Project = self.env["fedex.project"]
        active_domain = [("active", "=", True)]
        data = {
            "total_projects": Project.search_count(active_domain),
            "active_projects": Project.search_count(active_domain + [("state", "not in", ["completed", "cancelled"])]),
            "completed_projects": Project.search_count(active_domain + [("state", "=", "completed")]),
            "new_projects": Project.search_count(active_domain + [("state", "=", "new_project")]),
            "nearing": Project.search_count([("active", "=", True), ("is_nearing_completion", "=", True)]),
            "missing_documents": self.env["fedex.document.requirement"].search_count([("active", "=", True), ("state", "=", "missing")]),
            "overdue_milestones": self.env["fedex.milestone"].search_count([("state", "=", "overdue"), ("project_id.active", "=", True)]),
            "students": self.env["fedex.student"].search_count([]),
            "active_interns": self.env["fedex.project.member"].search_count([("state", "=", "active"), ("is_internship", "=", True)]),
            "by_status": [{"state": (r.get("state") or "Undefined"), "id_count": r.get("id_count", r.get("state_count", r.get("id", 0)))} for r in Project.read_group(active_domain, ["id:count"], ["state"])],
            "by_category": [{"category_ids": (r["category_ids"][1] if isinstance(r.get("category_ids"), (list, tuple)) and len(r["category_ids"]) > 1 else "Uncategorised"), "id_count": r.get("id_count", r.get("category_ids_count", r.get("id", 0)))} for r in Project.read_group(active_domain, ["id:count"], ["category_ids"])],
            "by_vertical": [{"vertical": r.get("vertical") or "unassigned", "id_count": r.get("id_count", r.get("vertical_count", r.get("id", 0)))} for r in Project.read_group(active_domain, ["id:count"], ["vertical"])],
            "by_type": [{"type_id": (r.get("type_id") and r["type_id"][1] or "Unassigned"), "id_count": r.get("id_count", r.get("type_id_count", r.get("id", 0)))} for r in Project.read_group(active_domain, ["id:count"], ["type_id"])],
            "recent": [{
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "state": p.state,
                "state_label": dict(p._fields["state"].selection).get(p.state, p.state),
                "supervisor_name": p.supervisor_id.name or "",
                "supervisor_partner_id": p.supervisor_id.partner_id.id or False,
            } for p in Project.search(active_domain, order="write_date desc", limit=8)],
        }
        return data

    @api.model
    def global_search(self, query):
        query = (query or "").strip()
        if not query:
            return []
        results = []
        searches = [
            ("fedex.project", ["|", ("name", "ilike", query), ("code", "ilike", query)], lambda r: f"Project: {r.code} · {r.name}", lambda r: False),
            ("fedex.student", ["|", ("name", "ilike", query), ("student_code", "ilike", query)], lambda r: f"Student: {r.student_code} · {r.name}", lambda r: f"/web/image/res.partner/{r.partner_id.id}/avatar_128"),
            ("fedex.faculty", ["|", ("name", "ilike", query), ("faculty_code", "ilike", query)], lambda r: f"Faculty: {r.faculty_code} · {r.name}", lambda r: f"/web/image/res.partner/{r.partner_id.id}/avatar_128"),
            ("fedex.staff", ["|", ("name", "ilike", query), ("staff_code", "ilike", query)], lambda r: f"Staff: {r.staff_code} · {r.name}", lambda r: f"/web/image/res.partner/{r.partner_id.id}/avatar_128"),
            ("fedex.document", ["|", ("name", "ilike", query), ("filename", "ilike", query)], lambda r: f"Document: {r.name}", lambda r: False),
        ]
        for model_name, domain, label, avatar_fn in searches:
            model = self.env[model_name]
            for rec in model.search(domain, limit=10):
                results.append({"id": rec.id, "label": label(rec), "model": model_name, "avatar_url": avatar_fn(rec)})
        return results


class FedexProjectMember(models.Model):
    _name = "fedex.project.member"
    _description = "Project Member"
    _order = "project_id,start_date desc"

    project_id = fields.Many2one("fedex.project", required=True, ondelete="cascade", index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True, ondelete="restrict")
    image_1920 = fields.Image(related="partner_id.image_1920", readonly=False, string="Photograph")
    avatar_128 = fields.Image(related="partner_id.avatar_128", string="Avatar")
    role_id = fields.Many2one("fedex.project.role", required=True, index=True, ondelete="restrict")
    start_date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    expected_end_date = fields.Date(index=True)
    actual_end_date = fields.Date()
    state = fields.Selection([("active", "Active"), ("completed", "Completed"), ("dropped", "Dropped")], default="active", required=True, index=True)
    certificate_issued = fields.Boolean()
    person_type_display = fields.Char(related="partner_id.person_type_display", store=True, index=True)
    project_state = fields.Selection(related="project_id.state", store=True)
    is_internship = fields.Boolean(related="project_id.is_internship", store=True, index=True)
    centre_id = fields.Many2one(related="project_id.centre_id", store=True, index=True)
    document_ids = fields.One2many("fedex.document", "member_id", domain=[("active", "=", True)])
    requirement_ids = fields.One2many("fedex.document.requirement", "member_id", domain=[("active", "=", True)])

    _sql_constraints = [("member_unique", "unique(project_id,partner_id,role_id,start_date)", "The same person, role and start date can only occur once on a project.")]

    @api.depends("project_id", "partner_id", "role_id", "start_date")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s · %s" % (rec.project_id.code, rec.partner_id.name, rec.role_id.name)

    @api.constrains("expected_end_date", "actual_end_date", "start_date")
    def _check_dates(self):
        for rec in self:
            if rec.expected_end_date and rec.expected_end_date < rec.start_date:
                raise ValidationError("Expected end date cannot be before start date.")
            if rec.actual_end_date and rec.actual_end_date < rec.start_date:
                raise ValidationError("Actual end date cannot be before start date.")

    @api.constrains("partner_id", "role_id")
    def _check_role_group(self):
        for rec in self:
            profiles = {"student": rec.partner_id.is_student, "faculty": rec.partner_id.is_faculty, "staff": rec.partner_id.is_staff}
            if not profiles.get(rec.role_id.role_group, False):
                raise ValidationError("The selected person's profile does not match the role group.")

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        self.env["fedex.document.requirement"]._sync_requirements(recs)
        return recs

    def write(self, vals):
        projects = self.mapped("project_id")
        result = super().write(vals)
        if set(vals) & {"role_id", "partner_id", "project_id"}:
            self.env["fedex.document.requirement"]._sync_requirements(projects | self.mapped("project_id"))
        return result

    def unlink(self):
        projects = self.mapped("project_id")
        result = super().unlink()
        self.env["fedex.document.requirement"]._sync_requirements(projects)
        return result


class FedexMilestone(models.Model):
    _name = "fedex.milestone"
    _description = "Project Milestone"
    _order = "due_date,name"

    project_id = fields.Many2one("fedex.project", required=True, ondelete="cascade", index=True)
    name = fields.Char(required=True)
    due_date = fields.Date(index=True)
    done = fields.Boolean()
    state = fields.Selection([("pending", "Pending"), ("done", "Done"), ("overdue", "Overdue")], compute="_compute_state", search="_search_state")

    @api.depends("project_id", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s" % (rec.project_id.code, rec.name)

    @api.depends("due_date", "done")
    def _compute_state(self):
        today = date.today()
        for rec in self:
            rec.state = "done" if rec.done else ("overdue" if rec.due_date and rec.due_date < today else "pending")

    def _search_state(self, operator, value):
        today = date.today()
        if operator in ("=", "=="):
            if value == "done":
                return [("done", "=", True)]
            elif value == "overdue":
                return [("done", "=", False), ("due_date", "!=", False), ("due_date", "<", today)]
            elif value == "pending":
                return [("done", "=", False), "|", ("due_date", "=", False), ("due_date", ">=", today)]
        elif operator in ("!=", "<>"):
            if value == "done":
                return [("done", "=", False)]
            elif value == "overdue":
                return ["|", ("done", "=", True), "|", ("due_date", "=", False), ("due_date", ">=", today)]
            elif value == "pending":
                return ["|", ("done", "=", True), "&", ("due_date", "!=", False), ("due_date", "<", today)]
        return []
