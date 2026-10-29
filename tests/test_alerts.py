from datetime import date, timedelta
from odoo.tests.common import TransactionCase


class TestFedexAlerts(TransactionCase):
    def test_alert_condition_is_idempotent_and_changes_with_date(self):
        project = self.env["fedex.project"].create({"name": "Alert Project", "centre_id": self.env["fedex.centre"].search([], limit=1).id, "type_id": self.env["fedex.project.type"].search([], limit=1).id, "state": "in_progress", "expected_end_date": date.today() + timedelta(days=1)})
        log = self.env["fedex.alert.log"]
        log._fire("nearing_completion", f"project:{project.id}:{project.expected_end_date}", project, None)
        log._fire("nearing_completion", f"project:{project.id}:{project.expected_end_date}", project, None)
        self.assertEqual(log.search_count([("alert_type", "=", "nearing_completion"), ("project_id", "=", project.id)]), 1)
        log._fire("nearing_completion", f"project:{project.id}:{date.today() + timedelta(days=2)}", project, None)
        self.assertEqual(log.search_count([("alert_type", "=", "nearing_completion"), ("project_id", "=", project.id)]), 2)
