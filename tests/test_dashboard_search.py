from odoo.tests.common import TransactionCase


class TestFedexDashboardSearch(TransactionCase):
    def test_dashboard_returns_all_required_metrics(self):
        data = self.env["fedex.project"].dashboard_data()
        for key in ("active_projects", "nearing", "missing_documents", "overdue_milestones", "students", "active_interns", "by_status", "by_category", "recent"):
            self.assertIn(key, data)

    def test_global_search_empty_and_accessible(self):
        self.assertEqual(self.env["fedex.project"].global_search(""), [])
        self.assertIsInstance(self.env["fedex.project"].global_search("Demo"), list)
