from datetime import date
from odoo import api, fields, models


class FedexAlertLog(models.Model):
    _name = "fedex.alert.log"
    _description = "FedEx Alert Log"
    _order = "triggered_at desc"

    alert_type = fields.Selection([("nearing_completion", "Nearing Completion"), ("member_ended", "Member Ended"), ("missing_internship_doc", "Missing Internship Document")], required=True, index=True)
    project_id = fields.Many2one("fedex.project", index=True, ondelete="cascade")
    member_id = fields.Many2one("fedex.project.member", index=True, ondelete="cascade")
    condition_key = fields.Char(required=True, index=True)
    triggered_at = fields.Datetime(default=fields.Datetime.now, required=True)
    recipient_ids = fields.Many2many("res.users", "fedex_alert_recipient_rel", "alert_id", "user_id")

    @api.depends("alert_type", "condition_key")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s · %s" % (rec.alert_type, rec.condition_key)

    _sql_constraints = [("alert_condition_uniq", "unique(alert_type,condition_key)", "This alert has already been logged for this condition.")]

    @api.model
    def _cron_daily(self):
        Project = self.env["fedex.project"]
        Member = self.env["fedex.project.member"]
        project_model = Project.search([])
        project_model._compute_days()
        req_model = self.env["fedex.document.requirement"]
        req_model._sync_requirements(project_model)
        for model_name in ("fedex.student", "fedex.faculty", "fedex.staff"):
            req_model._sync_requirements(self.env[model_name].search([]))

        threshold = int(self.env["fedex.repository.settings"]._get_param("nearing_days", 30))
        today = date.today()
        projects = Project.search([("state", "=", "in_progress"), ("expected_end_date", "!=", False)])
        for project in projects:
            if 0 <= (project.expected_end_date - today).days <= threshold:
                self._fire("nearing_completion", f"project:{project.id}:{project.expected_end_date}", project, None)
        for member in Member.search([("state", "=", "active"), ("expected_end_date", "<", today)]):
            self._fire("member_ended", f"member:{member.id}:{member.expected_end_date}", member.project_id, member)
        for member in Member.search([("state", "=", "active"), ("project_id.is_internship", "=", True), ("expected_end_date", "!=", False)]):
            if (member.expected_end_date - today).days <= threshold:
                for req in member.requirement_ids.filtered(lambda r: r.active and r.state == "missing" and r.doc_type_id.is_mandatory):
                    self._fire("missing_internship_doc", f"member:{member.id}:doc:{req.doc_type_id.id}", member.project_id, member, req.doc_type_id)
        return True

    def _recipients(self, project):
        users = self.env["res.users"].browse()
        if project.supervisor_id and project.supervisor_id.user_ids:
            users |= project.supervisor_id.user_ids
        coordinator_group = self.env.ref("fedex_repository.group_coordinator")
        users |= self.env["res.users"].search([("fedex_centre_ids", "in", project.centre_id.id), ("groups_id", "in", coordinator_group.id)])
        return users

    def _fire(self, alert_type, key, project, member, doc_type=None):
        if self.search_count([("alert_type", "=", alert_type), ("condition_key", "=", key)]):
            return False
        recipients = self._recipients(project)
        log = self.create({"alert_type": alert_type, "condition_key": key, "project_id": project.id, "member_id": member.id if member else False, "recipient_ids": [(6, 0, recipients.ids)]})
        activity_type = self.env.ref("mail.mail_activity_data_todo")
        target = project
        if not target and member:
            target = member
        for user in recipients:
            target.activity_schedule(activity_type.id, user_id=user.id, summary="FedEx Repository: %s" % dict(self._fields["alert_type"].selection).get(alert_type), note="Condition: %s" % key)
        return log
