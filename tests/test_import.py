import base64
import io
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestFedexImport(TransactionCase):
    def test_preview_does_not_write(self):
        content = "name,email,degree,institution,department,year_of_study,grading_scale,cgpa,status,technical_skills,soft_skills,domain_skills,student_code,phone\nPreview User,preview@example.com,BTech Computer Science,Demo Institute Alpha,Computer Science,2,cgpa10,8,applicant,,,,STU/PREVIEW/0001,"
        wizard = self.env["fedex.import.wizard"].create({"entity": "students", "filename": "students.csv", "file": base64.b64encode(content.encode())})
        before = self.env["fedex.student"].search_count([("email", "=", "preview@example.com")])
        wizard.action_validate()
        after = self.env["fedex.student"].search_count([("email", "=", "preview@example.com")])
        self.assertEqual(before, after)
        self.assertEqual(wizard.state, "preview")
        self.assertEqual(len(wizard.preview_line_ids), 1)

    def test_unknown_lookup_is_error_without_create(self):
        content = "name,email,degree,institution,department,year_of_study,grading_scale,cgpa,status,technical_skills,soft_skills,domain_skills,student_code,phone\nBad User,badimport@example.com,UNKNOWN DEGREE,Demo Institute Alpha,Computer Science,2,cgpa10,8,applicant,,,,STU/PREVIEW/0002,"
        wizard = self.env["fedex.import.wizard"].create({"entity": "students", "filename": "students.csv", "file": base64.b64encode(content.encode())})
        wizard.action_validate()
        self.assertEqual(wizard.preview_line_ids.status, "error")
