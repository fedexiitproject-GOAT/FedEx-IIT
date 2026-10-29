from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"
    fedex_centre_ids = fields.Many2many(
        "fedex.centre", "fedex_user_centre_rel", "user_id", "centre_id", string="FedEx Centres", index=True
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    person_type_display = fields.Char(compute="_compute_person_type_display", store=True, index=True)
    is_student = fields.Boolean(compute="_compute_person_type_display")
    is_faculty = fields.Boolean(compute="_compute_person_type_display")
    is_staff = fields.Boolean(compute="_compute_person_type_display")
    student_profile_ids = fields.One2many("fedex.student", "partner_id")
    faculty_profile_ids = fields.One2many("fedex.faculty", "partner_id")
    staff_profile_ids = fields.One2many("fedex.staff", "partner_id")
    project_member_ids = fields.One2many("fedex.project.member", "partner_id")

    @api.depends("student_profile_ids.active", "faculty_profile_ids.active", "staff_profile_ids.active")
    def _compute_person_type_display(self):
        for rec in self:
            labels = []
            if rec.student_profile_ids.filtered("active"):
                labels.append("Student")
            if rec.faculty_profile_ids.filtered("active"):
                labels.append("Faculty")
            if rec.staff_profile_ids.filtered("active"):
                labels.append("Staff")
            rec.person_type_display = ", ".join(labels)
            rec.is_student = bool(rec.student_profile_ids.filtered("active"))
            rec.is_faculty = bool(rec.faculty_profile_ids.filtered("active"))
            rec.is_staff = bool(rec.staff_profile_ids.filtered("active"))

    def _open_profile(self, model):
        self.ensure_one()
        profile = self.env[model].search([("partner_id", "=", self.id)], limit=1)
        if not profile:
            return False
        return {"type": "ir.actions.act_window", "res_model": model, "res_id": profile.id, "view_mode": "form"}

    def action_open_student_profiles(self):
        return self._open_profile("fedex.student")

    def action_open_faculty_profiles(self):
        return self._open_profile("fedex.faculty")

    def action_open_staff_profiles(self):
        return self._open_profile("fedex.staff")
