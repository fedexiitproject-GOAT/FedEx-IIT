import base64
from datetime import date
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFedexDocuments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Project = cls.env["fedex.project"]
        cls.Member = cls.env["fedex.project.member"]
        cls.Student = cls.env["fedex.student"]
        cls.Partner = cls.env["res.partner"]
        cls.Role = cls.env["fedex.project.role"]
        cls.DocType = cls.env["fedex.document.type"]
        cls.Doc = cls.env["fedex.document"]
        cls.Req = cls.env["fedex.document.requirement"]

    def _student(self, suffix="doc"):
        institution = self.env["fedex.institution"].search([], limit=1)
        degree = self.env["fedex.degree"].search([], limit=1)
        department = self.env["fedex.department"].search([("institution_id", "=", institution.id)], limit=1)
        return self.Student.create({"name": "Document Student %s" % suffix, "email": "%s@example.com" % suffix, "degree_id": degree.id, "institution_id": institution.id, "department_id": department.id, "grading_scale": "cgpa10", "cgpa": 8})

    def _project(self, student):
        project = self.Project.create({"name": "Document Project", "centre_id": self.env["fedex.centre"].search([], limit=1).id, "type_id": self.env.ref("fedex_repository.type_summer").id, "start_date": date.today()})
        role = self.Role.search([("name", "=", "Intern")], limit=1)
        member = self.Member.create({"project_id": project.id, "partner_id": student.partner_id.id, "role_id": role.id, "start_date": date.today()})
        return project, member

    def test_document_scope_is_enforced(self):
        student = self._student("scope")
        project, member = self._project(student)
        project_type = self.DocType.search([("scope", "=", "project")], limit=1)
        with self.assertRaises(ValidationError):
            self.Doc.create({"doc_type_id": project_type.id, "partner_id": student.partner_id.id, "filename": "x.txt", "file": base64.b64encode(b"x")})

    def test_engagement_documents_are_separate(self):
        student = self._student("engagement")
        project = self.Project.create({"name": "Two Engagements", "centre_id": self.env["fedex.centre"].search([], limit=1).id, "type_id": self.env.ref("fedex_repository.type_summer").id})
        intern = self.Role.search([("name", "=", "Intern")], limit=1)
        researcher = self.Role.search([("name", "=", "Researcher")], limit=1)
        member1 = self.Member.create({"project_id": project.id, "partner_id": student.partner_id.id, "role_id": intern.id, "start_date": date(2026, 1, 1)})
        member2 = self.Member.create({"project_id": project.id, "partner_id": student.partner_id.id, "role_id": researcher.id, "start_date": date(2026, 2, 1)})
        dtype = self.DocType.search([("scope", "=", "engagement")], limit=1)
        doc1 = self.Doc.create({"doc_type_id": dtype.id, "member_id": member1.id, "filename": "one.txt", "file": base64.b64encode(b"one")})
        doc2 = self.Doc.create({"doc_type_id": dtype.id, "member_id": member2.id, "filename": "two.txt", "file": base64.b64encode(b"two")})
        self.assertNotEqual(doc1.member_id, doc2.member_id)
        self.assertEqual(doc1.project_id, project)
        self.assertEqual(doc2.partner_id, student.partner_id)

    def test_requirement_sync_idempotent_and_version_rebinds(self):
        student = self._student("idempotent")
        project, member = self._project(student)
        dtype = self.DocType.search([("name", "=", "Completion Certificate")], limit=1)
        self.Req._sync_requirements(member)
        self.Req._sync_requirements(member)
        reqs = self.Req.search([("doc_type_id", "=", dtype.id), ("member_id", "=", member.id)])
        self.assertEqual(len(reqs), 1)
        doc = self.Doc.create({"doc_type_id": dtype.id, "member_id": member.id, "filename": "v1.txt", "file": base64.b64encode(b"v1")})
        self.assertEqual(reqs.document_id, doc)
        replacement = self.env["fedex.document.replace.wizard"].create({"document_id": doc.id, "filename": "v2.txt", "file": base64.b64encode(b"v2")})
        action = replacement.action_replace()
        reqs.invalidate_recordset(["document_id", "state"])
        self.assertEqual(reqs.document_id.version, 2)
        self.assertEqual(reqs.state, "uploaded")

    def test_requirement_archiving_and_reactivation(self):
        student = self._student("archive")
        project, member = self._project(student)
        dtype = self.DocType.search([("name", "=", "Completion Certificate")], limit=1)
        self.Req._sync_requirements(member)
        req = self.Req.search([("doc_type_id", "=", dtype.id), ("member_id", "=", member.id)], limit=1)
        doc = self.Doc.create({"doc_type_id": dtype.id, "member_id": member.id, "filename": "x.txt", "file": base64.b64encode(b"x")})
        req._sync_requirements(member)
        dtype.applies_to_type_ids = [(5, 0, 0)]
        self.Req._sync_requirements(member)
        self.assertFalse(req.active)
        dtype.applies_to_type_ids = [(4, self.env.ref("fedex_repository.type_summer").id)]
        self.Req._sync_requirements(member)
        self.assertTrue(req.active)
        self.assertEqual(self.Req.search_count([("doc_type_id", "=", dtype.id), ("owner_key", "=", req.owner_key)]), 1)
