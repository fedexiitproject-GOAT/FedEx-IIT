from odoo import api, fields, models
from odoo.exceptions import ValidationError


class _FedexProfileMixin:
    def _get_placeholder_filename(self, field=None):
        if field in ("image_1920", "image_1024", "image_512", "image_256", "image_128", "avatar_1920", "avatar_1024", "avatar_512", "avatar_256", "avatar_128"):
            return "base/static/img/avatar_grey.png"
        return super()._get_placeholder_filename(field=field)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name
            self.email = self.partner_id.email
            self.phone = self.partner_id.phone

    @api.model
    def _prepare_partner(self, vals):
        vals = dict(vals)
        partner_id = vals.get("partner_id")
        if partner_id:
            partner_updates = {"is_company": False}
            if vals.get("image_1920"):
                partner_updates["image_1920"] = vals.pop("image_1920")
            for k in ("name", "email", "phone", "mobile"):
                if vals.get(k):
                    partner_updates[k] = vals.pop(k)
            self.env["res.partner"].browse(partner_id).write(partner_updates)
            return vals
        email = (vals.get("email") or "").strip()
        if email:
            partner = self.env["res.partner"].search([("email", "=ilike", email)], limit=1)
            if partner:
                partner_updates = {"is_company": False}
                if vals.get("image_1920"):
                    partner_updates["image_1920"] = vals.pop("image_1920")
                partner.write(partner_updates)
                vals["partner_id"] = partner.id
                return vals
        partner_vals = {k: vals.pop(k) for k in ("name", "email", "phone", "mobile", "street", "street2", "city", "zip", "state_id", "country_id", "company_type", "is_company", "image_1920") if k in vals}
        partner_vals.setdefault("name", vals.get("name") or "Unnamed")
        partner_vals["is_company"] = False
        partner_vals["company_type"] = "person"
        vals["partner_id"] = self.env["res.partner"].create(partner_vals).id
        return vals


class FedexStudent(_FedexProfileMixin, models.Model):
    _name = "fedex.student"
    _description = "FedEx Student"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "student_code"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade", index=True, domain=[("is_company", "=", False)])
    student_code = fields.Char(required=True, default="New", copy=False, index=True)
    degree_id = fields.Many2one("fedex.degree", required=True, index=True)
    institution_id = fields.Many2one("fedex.institution", required=True, index=True)
    department_id = fields.Many2one("fedex.department", index=True)
    year_of_study = fields.Integer()
    grading_scale = fields.Selection([("cgpa10", "CGPA / 10"), ("percentage", "Percentage")], required=True)
    cgpa = fields.Float()
    technical_skill_ids = fields.Many2many("fedex.skill", "fedex_student_technical_skill_rel", "student_id", "skill_id", domain=[("skill_type", "=", "technical")])
    soft_skill_ids = fields.Many2many("fedex.skill", "fedex_student_soft_skill_rel", "student_id", "skill_id", domain=[("skill_type", "=", "soft")])
    domain_ids = fields.Many2many("fedex.skill", "fedex_student_domain_skill_rel", "student_id", "skill_id", domain=[("skill_type", "=", "domain")])
    status = fields.Selection([("applicant", "Applicant"), ("active", "Active"), ("completed", "Completed"), ("alumni", "Alumni")], default="applicant", required=True, tracking=True)
    active = fields.Boolean(default=True)
    member_ids = fields.Many2many("fedex.project.member", compute="_compute_related_records", string="Project Engagements")
    document_ids = fields.Many2many("fedex.document", compute="_compute_related_records", string="Documents")
    requirement_ids = fields.One2many("fedex.document.requirement", "partner_id", domain=[("active", "=", True)])
    project_count = fields.Integer(compute="_compute_counts")
    _sql_constraints = [("student_code_uniq", "unique(student_code)", "Student code must be unique.")]
    missing_doc_count = fields.Integer(compute="_compute_counts", search="_search_missing_doc_count")

    @api.depends("name", "student_code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s" % (rec.student_code, rec.name)

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            vals = self._prepare_partner(vals)
            if vals.get("student_code") in (None, "New"):
                vals["student_code"] = self.env["ir.sequence"].next_by_code("fedex.student") or "New"
            prepared.append(vals)
        recs = super().create(prepared)
        self.env["fedex.document.requirement"]._sync_requirements(recs)
        return recs

    def _compute_related_records(self):
        Member = self.env["fedex.project.member"]
        Document = self.env["fedex.document"]
        for rec in self:
            rec.member_ids = Member.search([("partner_id", "=", rec.partner_id.id)])
            rec.document_ids = Document.search([("partner_id", "=", rec.partner_id.id)])

    def _compute_counts(self):
        Req = self.env["fedex.document.requirement"]
        Member = self.env["fedex.project.member"]
        for rec in self:
            members = Member.search([("partner_id", "=", rec.partner_id.id)])
            rec.project_count = len(members.mapped("project_id"))
            rec.missing_doc_count = Req.search_count([("partner_id", "=", rec.partner_id.id), ("active", "=", True), ("state", "=", "missing")])

    def _search_missing_doc_count(self, operator, value):
        reqs = self.env["fedex.document.requirement"].search([("active", "=", True), ("state", "=", "missing")])
        partner_ids = reqs.mapped("partner_id").ids
        if (operator in (">", "!=") and value == 0) or (operator == ">=" and value == 1):
            return [("partner_id", "in", partner_ids)]
        elif (operator == "=" and value == 0) or (operator == "<=" and value == 0):
            return [("partner_id", "not in", partner_ids)]
        return []

    @api.constrains("email")
    def _unique_student_email(self):
        for rec in self:
            if rec.email:
                duplicate = self.search([("email", "=ilike", rec.email), ("id", "!=", rec.id)], limit=1)
                if duplicate:
                    raise ValidationError("Student email must be unique among students.")

    @api.constrains("cgpa", "grading_scale")
    def _check_cgpa(self):
        for rec in self:
            if rec.cgpa < 0 or (rec.grading_scale == "cgpa10" and rec.cgpa > 10) or (rec.grading_scale == "percentage" and rec.cgpa > 100):
                raise ValidationError("CGPA / percentage is outside the allowed range.")

    @api.constrains("year_of_study")
    def _check_year(self):
        for rec in self:
            if rec.year_of_study and not 1 <= rec.year_of_study <= 5:
                raise ValidationError("Year of study must be between 1 and 5.")

    @api.constrains("department_id", "institution_id")
    def _check_department_institution(self):
        for rec in self:
            if rec.department_id and rec.department_id.institution_id != rec.institution_id:
                raise ValidationError("Department must belong to the selected institution.")

    def action_open_projects(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": "Projects", "res_model": "fedex.project", "view_mode": "list,kanban,form", "domain": [("member_ids.partner_id", "=", self.partner_id.id)]}


class FedexFaculty(_FedexProfileMixin, models.Model):
    _name = "fedex.faculty"
    _description = "FedEx Faculty"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "faculty_code"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade", index=True, domain=[("is_company", "=", False)])
    faculty_code = fields.Char(required=True, default="New", copy=False, index=True)
    institution_id = fields.Many2one("fedex.institution", required=True, index=True)
    department_id = fields.Many2one("fedex.department", index=True)
    category_ids = fields.Many2many("fedex.project.category", string="Project Categories")
    active = fields.Boolean(default=True)
    project_count = fields.Integer(compute="_compute_project_count")
    supervised_project_ids = fields.One2many("fedex.project", "supervisor_id", string="Supervised Projects")
    requirement_ids = fields.One2many("fedex.document.requirement", "partner_id", domain=[("active", "=", True)])
    _sql_constraints = [("faculty_code_uniq", "unique(faculty_code)", "Faculty code must be unique.")]

    @api.depends("name", "faculty_code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s" % (rec.faculty_code, rec.name)

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            vals = self._prepare_partner(vals)
            if vals.get("faculty_code") in (None, "New"):
                vals["faculty_code"] = self.env["ir.sequence"].next_by_code("fedex.faculty") or "New"
            prepared.append(vals)
        recs = super().create(prepared)
        self.env["fedex.document.requirement"]._sync_requirements(recs)
        return recs

    def _compute_project_count(self):
        Project = self.env["fedex.project"]
        for rec in self:
            rec.project_count = Project.search_count(["|", ("supervisor_id", "=", rec.id), ("member_ids.partner_id", "=", rec.partner_id.id)])

    @api.constrains("department_id", "institution_id")
    def _check_department_institution(self):
        for rec in self:
            if rec.department_id and rec.department_id.institution_id != rec.institution_id:
                raise ValidationError("Department must belong to the selected institution.")

    def action_open_projects(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": "Projects", "res_model": "fedex.project", "view_mode": "list,kanban,form", "domain": ["|", ("supervisor_id", "=", self.id), ("member_ids.partner_id", "=", self.partner_id.id)]}


class FedexStaff(_FedexProfileMixin, models.Model):
    _name = "fedex.staff"
    _description = "FedEx Staff"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "staff_code"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade", index=True, domain=[("is_company", "=", False)])
    staff_code = fields.Char(required=True, default="New", copy=False, index=True)
    designation = fields.Char()
    department_id = fields.Many2one("fedex.department", index=True)
    active = fields.Boolean(default=True)
    requirement_ids = fields.One2many("fedex.document.requirement", "partner_id", domain=[("active", "=", True)])
    _sql_constraints = [("staff_code_uniq", "unique(staff_code)", "Staff code must be unique.")]

    @api.depends("name", "staff_code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s" % (rec.staff_code, rec.name)

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            vals = self._prepare_partner(vals)
            if vals.get("staff_code") in (None, "New"):
                vals["staff_code"] = self.env["ir.sequence"].next_by_code("fedex.staff") or "New"
            prepared.append(vals)
        recs = super().create(prepared)
        self.env["fedex.document.requirement"]._sync_requirements(recs)
        return recs
