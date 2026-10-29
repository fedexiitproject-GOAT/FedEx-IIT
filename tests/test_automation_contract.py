from odoo.tests.common import TransactionCase


class TestFedexAutomationContract(TransactionCase):
    def test_cron_is_daily_and_uses_no_legacy_fields(self):
        cron = self.env.ref("fedex_repository.ir_cron_fedex_daily")
        self.assertEqual(cron.interval_type, "days")
        self.assertEqual(cron.interval_number, 1)
        self.assertFalse("numbercall" in cron._fields)
        self.assertFalse("doall" in cron._fields)
