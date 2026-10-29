from odoo import api, fields, models
from odoo.exceptions import ValidationError

class FedexDisplayNameMixin(models.AbstractModel):
    _name = "fedex.display.name.mixin"
    _description = "FedEx Display Name Mixin"

    @api.depends("name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name or "%s #%s" % (rec._description, rec.id)


class FedexNamedMaster(models.AbstractModel):
    _name = "fedex.named.master"
    _description = "FedEx Named Master"
    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

class FedexInstitution(FedexDisplayNameMixin, models.Model):
    _name="fedex.institution"; _description="Institution"; _order="name"
    name=fields.Char(required=True); short_code=fields.Char(); active=fields.Boolean(default=True)
    _sql_constraints=[("name_uniq","unique(name)","Institution name must be unique.")]
class FedexDepartment(FedexDisplayNameMixin, models.Model):
    _name="fedex.department"; _description="Department"; _order="name"
    name=fields.Char(required=True); institution_id=fields.Many2one("fedex.institution",required=True,ondelete="restrict",index=True); active=fields.Boolean(default=True)
    _sql_constraints=[("name_inst_uniq","unique(name,institution_id)","Department must be unique within an institution.")]
class FedexDegree(FedexDisplayNameMixin, models.Model):
    _name="fedex.degree"; _description="Degree"; _order="name"
    name=fields.Char(required=True); active=fields.Boolean(default=True)
    _sql_constraints=[("name_uniq","unique(name)","Degree name must be unique.")]
class FedexSkill(FedexDisplayNameMixin, models.Model):
    _name="fedex.skill"; _description="Skill"; _order="name"
    name=fields.Char(required=True); skill_type=fields.Selection([("technical","Technical"),("soft","Soft"),("domain","Domain")],required=True); active=fields.Boolean(default=True)
    _sql_constraints=[("name_type_uniq","unique(name,skill_type)","Skill must be unique within its type.")]
class FedexCentre(FedexDisplayNameMixin, models.Model):
    _name="fedex.centre"; _description="FedEx Centre"; _order="name"
    name=fields.Char(required=True); active=fields.Boolean(default=True)
    _sql_constraints=[("name_uniq","unique(name)","Centre name must be unique.")]
class FedexProjectType(FedexDisplayNameMixin, models.Model):
    _name="fedex.project.type"; _description="Project Type"; _order="name"
    name=fields.Char(required=True); is_internship=fields.Boolean(default=False); active=fields.Boolean(default=True)
    _sql_constraints=[("name_uniq","unique(name)","Project type must be unique.")]
class FedexProjectCategory(FedexDisplayNameMixin, models.Model):
    _name="fedex.project.category"; _description="Project Category"; _order="name"
    name=fields.Char(required=True); color=fields.Integer(); active=fields.Boolean(default=True)
    _sql_constraints=[("name_uniq","unique(name)","Project category must be unique.")]
class FedexSponsor(FedexDisplayNameMixin, models.Model):
    _name="fedex.sponsor"; _description="Sponsor"; _order="name"
    name=fields.Char(required=True); partner_id=fields.Many2one("res.partner",index=True); active=fields.Boolean(default=True)
class FedexProjectRole(FedexDisplayNameMixin, models.Model):
    _name="fedex.project.role"; _description="Project Role"; _order="role_group,name"
    name=fields.Char(required=True); role_group=fields.Selection([("student","Student"),("faculty","Faculty"),("staff","Staff")],required=True); active=fields.Boolean(default=True)
class FedexDocumentType(FedexDisplayNameMixin, models.Model):
    _name="fedex.document.type"; _description="Document Type"; _order="scope,name"
    name=fields.Char(required=True); active=fields.Boolean(default=True)
    scope=fields.Selection([("person","Person"),("project","Project"),("engagement","Engagement")],required=True)
    applies_to_person=fields.Selection([("student","Student"),("faculty","Faculty"),("staff","Staff"),("all","All")],default="student",required=True)
    is_mandatory=fields.Boolean()
    applies_to_type_ids=fields.Many2many("fedex.project.type", "fedex_doc_type_project_type_rel", "doc_type_id", "type_id", string="Project Types")
    @api.constrains("scope","applies_to_person")
    def _check_scope(self):
        for r in self:
            if r.scope=="project" and r.applies_to_person!="all":
                raise ValidationError("Project document types must apply to All persons.")
    @api.model_create_multi
    def create(self, vals_list):
        recs=super().create(vals_list)
        self.env["fedex.document.requirement"]._sync_requirements(recs)
        return recs
    def write(self, vals):
        res=super().write(vals)
        if set(vals) & {"active","scope","applies_to_person","is_mandatory","applies_to_type_ids"}:
            self.env["fedex.document.requirement"]._sync_requirements(self)
        return res
