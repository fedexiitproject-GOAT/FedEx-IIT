from odoo.tests.common import TransactionCase
class TestFedexRequirements(TransactionCase):
    def test_owner_key_is_unique(self):
        Req=self.env["fedex.document.requirement"]
        self.assertTrue("owner_key" in Req._fields)
