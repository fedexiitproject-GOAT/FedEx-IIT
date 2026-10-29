import io
from odoo import http
from odoo.http import request, content_disposition
try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None

TEMPLATES = {
    "students": ["student_code", "name", "email", "phone", "degree", "institution", "department", "year_of_study", "grading_scale", "cgpa", "status", "technical_skills", "soft_skills", "domain_skills"],
    "faculty": ["faculty_code", "name", "email", "phone", "institution", "department", "categories"],
    "staff": ["staff_code", "name", "email", "phone", "designation", "department"],
    "projects": ["code", "name", "description", "centre", "type", "categories", "sponsor", "supervisor_email", "state", "priority", "start_date", "expected_end_date", "actual_end_date", "progress_manual"],
    "project_members": ["project_code", "person_email", "role", "start_date", "expected_end_date", "actual_end_date", "state", "certificate_issued"],
}


class FedexImportController(http.Controller):
    @http.route("/fedex_repository/import/template/<string:entity>", type="http", auth="user", methods=["GET"])
    def template(self, entity, **kwargs):
        if entity not in TEMPLATES:
            return request.not_found()
        if not request.env.user.has_group("fedex_repository.group_repository_manager") and not request.env.user.has_group("fedex_repository.group_administrator"):
            return request.not_found()
        if Workbook is None:
            return request.make_response("openpyxl is not installed", status=500)
        wb = Workbook()
        ws = wb.active; ws.title = "Template"
        headers = TEMPLATES[entity]
        ws.append(headers)
        notes = wb.create_sheet("Notes")
        notes.append(["Column", "Notes"])
        for header in headers:
            notes.append([header, "Use the exact column name. Lookups are matched case-insensitively; unknown lookups require Create missing lookup values."])
        stream = io.BytesIO(); wb.save(stream); stream.seek(0)
        return request.make_response(stream.read(), headers=[("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), ("Content-Disposition", content_disposition(f"fedex_{entity}_template.xlsx"))])
