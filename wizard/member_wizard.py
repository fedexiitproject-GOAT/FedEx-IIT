from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FedexAddMemberWizard(models.TransientModel):
    _name = "fedex.add.member.wizard"
    _description = "Add Project Members"

    project_id = fields.Many2one("fedex.project", required=True, readonly=True)
    partner_ids = fields.Many2many("res.partner", string="People", required=True)
    role_id = fields.Many2one("fedex.project.role", required=True)
    start_date = fields.Date(required=True, default=fields.Date.context_today)
    expected_end_date = fields.Date()

    @api.onchange("role_id")
    def _onchange_role_id(self):
        if self.role_id:
            self.partner_ids = self.env["res.partner"].search([("is_%s" % self.role_id.role_group, "=", True)])

    @api.constrains("expected_end_date", "start_date")
    def _check_dates(self):
        for rec in self:
            if rec.expected_end_date and rec.expected_end_date < rec.start_date:
                raise ValidationError("Expected end date cannot be before start date.")

    def action_add(self):
        self.ensure_one()
        for partner in self.partner_ids:
            self.env["fedex.project.member"].create({"project_id": self.project_id.id, "partner_id": partner.id, "role_id": self.role_id.id, "start_date": self.start_date, "expected_end_date": self.expected_end_date})
        return {"type": "ir.actions.act_window_close"}
