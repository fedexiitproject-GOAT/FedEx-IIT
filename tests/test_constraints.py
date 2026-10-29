from datetime import date, timedelta
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFedexConstraints(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Project = cls.env["fedex.project"]
        cls.Centre = cls.env["fedex.centre"]
        cls.Type = cls.env["fedex.project.type"]
        cls.Student = cls.env["fedex.student"]
        cls.Degree = cls.env["fedex.degree"]
        cls.Institution = cls.env["fedex.institution"]
        cls.Department = cls.env["fedex.department"]
        cls.Role = cls.env["fedex.project.role"]
        cls.Partner = cls.env["res.partner"]

    def _student(self, email="constraint.student@example.com"):
        institution = self.Institution.search([], limit=1)
        degree = self.Degree.search([], limit=1)
        department = self.Department.search([("institution_id", "=", institution.id)], limit=1)
        return self.Student.create({"name": "Constraint Student", "email": email, "degree_id": degree.id, "institution_id": institution.id, "department_id": department.id, "grading_scale": "cgpa10", "cgpa": 8})

    def _project(self, **extra):
        vals = {"name": "Constraint Project", "centre_id": self.Centre.search([], limit=1).id, "type_id": self.Type.search([], limit=1).id}
        vals.update(extra)
        return self.Project.create(vals)

    def test_completed_requires_actual_end(self):
        project = self._project()
        with self.assertRaises(ValidationError):
            project.write({"state": "completed"})

    def test_project_date_range(self):
        with self.assertRaises(ValidationError):
            self._project(start_date=date.today(), expected_end_date=date.today() - timedelta(days=1))

    def test_cgpa_range(self):
        with self.assertRaises(ValidationError):
            self._student("bad.cgpa@example.com").write({"cgpa": 11})

    def test_student_email_unique(self):
        self._student("unique.student@example.com")
        with self.assertRaises(ValidationError):
            self._student("unique.student@example.com")

    def test_member_role_group_match(self):
        student = self._student("role.student@example.com")
        project = self._project()
        faculty_role = self.Role.search([("role_group", "=", "faculty")], limit=1)
        with self.assertRaises(ValidationError):
            self.env["fedex.project.member"].create({"project_id": project.id, "partner_id": student.partner_id.id, "role_id": faculty_role.id, "start_date": date.today()})

    def test_member_dates_and_uniqueness(self):
        student = self._student("member.student@example.com")
        project = self._project()
        role = self.Role.search([("role_group", "=", "student")], limit=1)
        vals = {"project_id": project.id, "partner_id": student.partner_id.id, "role_id": role.id, "start_date": date.today()}
        self.env["fedex.project.member"].create(vals)
        with self.assertRaises(Exception):
            self.env["fedex.project.member"].create(vals)
