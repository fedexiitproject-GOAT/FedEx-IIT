from odoo import fields, models


class FedexProjectResearchExtension(models.Model):
    _inherit = "fedex.project"

    about = fields.Html(string="About")
    overview = fields.Html(string="Overview")
    objectives = fields.Html(string="Objectives")
    methodology = fields.Html(string="Methodology")
    next_step = fields.Html(string="Next Step")
    vertical = fields.Selection([
        ("supply_chain", "Supply Chain Sustainability and Modelling"),
        ("worker_wellness", "Logistics Worker Wellness"),
        ("algorithms_ml", "Algorithms and Machine Learning"),
        ("infrastructure", "Logistics Infrastructure"),
    ], string="Research Vertical", index=True)
    state = fields.Selection(
        selection_add=[("new_project", "New Project")],
        ondelete={"new_project": "set default"},
    )


class FedexProjectMemberResearchExtension(models.Model):
    _inherit = "fedex.project.member"

    association_type = fields.Selection([
        ("lead_professor", "Lead Professor"),
        ("co_pi", "Co-Principal Investigator"),
        ("researcher", "Researcher"),
        ("phd_student", "PhD Student"),
        ("mtech_student", "MTech Student"),
        ("btech_student", "BTech Student"),
        ("postdoc_researcher", "Post Doctoral Researcher"),
    ], string="Association Type", index=True)


class ResPartnerFedexResearchExtension(models.Model):
    _inherit = "res.partner"

    people_role = fields.Selection([
        ("professor", "Professor"),
        ("researcher", "Researcher"),
        ("students", "Students"),
        ("staff", "Staff"),
        ("admin", "Admin"),
        ("postdoc", "Post doc"),
    ], string="FedEx People Role", index=True)
