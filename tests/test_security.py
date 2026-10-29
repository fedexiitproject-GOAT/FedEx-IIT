from odoo.tests.common import TransactionCase


class TestFedexSecurity(TransactionCase):
    def _user(self, name, group_xmlids):
        groups = [self.env.ref(x).id for x in group_xmlids]
        return self.env["res.users"].create({"name": name, "login": name.lower().replace(" ", ".") + "@example.com", "email": name.lower().replace(" ", ".") + "@example.com", "groups_id": [(6, 0, groups)]})

    def test_faculty_and_student_groups_do_not_imply_coordinator(self):
        faculty = self._user("Faculty Security", ["fedex_repository.group_faculty"])
        student = self._user("Student Security", ["fedex_repository.group_student"])
        self.assertFalse(faculty.has_group("fedex_repository.group_coordinator"))
        self.assertFalse(student.has_group("fedex_repository.group_coordinator"))

    def test_faculty_plus_coordinator_has_both(self):
        user = self._user("Faculty Coordinator", ["fedex_repository.group_faculty", "fedex_repository.group_coordinator"])
        self.assertTrue(user.has_group("fedex_repository.group_faculty"))
        self.assertTrue(user.has_group("fedex_repository.group_coordinator"))
