from odoo import fields, models
from odoo.exceptions import UserError


class FedexDocumentReplaceWizard(models.TransientModel):
    _name = "fedex.document.replace.wizard"
    _description = "Replace FedEx Document"

    document_id = fields.Many2one("fedex.document", required=True, readonly=True)
    file = fields.Binary(required=True)
    filename = fields.Char(required=True)

    def action_replace(self):
        self.ensure_one()
        old = self.document_id
        if not old.active:
            raise UserError("Only the latest active document can be replaced.")
        new = self.env["fedex.document"].create({
            "name": self.filename,
            "doc_type_id": old.doc_type_id.id,
            "project_id": old.project_id.id,
            "partner_id": old.partner_id.id,
            "member_id": old.member_id.id,
            "file": self.file,
            "filename": self.filename,
            "version": old.version + 1,
        })
        old.active = False
        note = "Document replaced: version %s → version %s (%s)." % (old.version, new.version, self.filename)
        old.message_post(body=note)
        new.message_post(body="Created as replacement for version %s." % old.version)
        if old.project_id:
            old.project_id.message_post(body=note)
        if old.partner_id:
            old.partner_id.message_post(body=note)
        return {"type": "ir.actions.act_window", "res_model": "fedex.document", "res_id": new.id, "view_mode": "form"}
