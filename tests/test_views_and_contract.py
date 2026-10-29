import ast
import csv
import os
import xml.etree.ElementTree as ET
from odoo.tests.common import TransactionCase


class TestFedexContract(TransactionCase):
    def test_required_models_exist(self):
        required = ["fedex.institution", "fedex.department", "fedex.degree", "fedex.skill", "fedex.centre", "fedex.project.type", "fedex.project.category", "fedex.sponsor", "fedex.project.role", "fedex.document.type", "fedex.student", "fedex.faculty", "fedex.staff", "fedex.project", "fedex.project.member", "fedex.milestone", "fedex.document", "fedex.document.requirement", "fedex.alert.log"]
        for model in required:
            self.assertIn(model, self.env)

    def test_required_roles_exist(self):
        for xmlid in ("group_administrator", "group_repository_manager", "group_coordinator", "group_faculty", "group_student", "group_management"):
            self.assertTrue(self.env.ref("fedex_repository." + xmlid))
