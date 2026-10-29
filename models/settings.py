from odoo import api, fields, models


class FedexRepositorySettings(models.TransientModel):
    _inherit = "res.config.settings"

    nearing_days = fields.Integer(default=30, string="Nearing Completion Threshold (days)")
    max_upload_mb = fields.Float(default=25, string="Maximum Upload Size (MB)")
    allowed_extensions = fields.Char(default="pdf,doc,docx,xls,xlsx,ppt,pptx,csv,txt,zip,png,jpg,jpeg,ipynb,py")

    @api.model
    def _get_param(self, key, default):
        return self.env["ir.config_parameter"].sudo().get_param(f"fedex_repository.{key}", default)

    @api.model
    def get_repository_config(self):
        return {
            "nearing_days": int(self._get_param("nearing_days", 30)),
            "max_upload_mb": float(self._get_param("max_upload_mb", 25)),
            "allowed_extensions": self._get_param("allowed_extensions", "pdf,doc,docx,xls,xlsx,ppt,pptx,csv,txt,zip,png,jpg,jpeg,ipynb,py"),
        }

    def get_values(self):
        res = super().get_values()
        cfg = self.get_repository_config()
        res.update(cfg)
        return res

    def set_values(self):
        super().set_values()
        p = self.env["ir.config_parameter"].sudo()
        p.set_param("fedex_repository.nearing_days", max(0, self.nearing_days))
        p.set_param("fedex_repository.max_upload_mb", max(0.1, self.max_upload_mb))
        p.set_param("fedex_repository.allowed_extensions", (self.allowed_extensions or "").lower())


class FedexRepositorySettingsAlias(models.AbstractModel):
    _name = "fedex.repository.settings"
    _description = "FedEx Repository Settings Helper"

    @api.model
    def _get_param(self, key, default):
        return self.env["res.config.settings"]._get_param(key, default)

    @api.model
    def get_repository_config(self):
        return self.env["res.config.settings"].get_repository_config()
