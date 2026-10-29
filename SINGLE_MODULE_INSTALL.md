# FedEx Data Repository — Single Odoo Module

This package contains exactly one installable Odoo addon: `fedex_repository`. The research fields, verticals, association types, people roles, project types, analytics views, and FedEx liquid-glass stylesheet are integrated into this module. There is no separate extension addon to install.

## Install / upgrade
1. Copy this `fedex_repository` folder into an Odoo 18 custom-addons directory.
2. Ensure `openpyxl` is installed in Odoo's Python environment if XLSX import is used.
3. Restart Odoo and update the Apps list.
4. If the module is already installed, back up the database and filestore, then upgrade with `-u fedex_repository`. Otherwise install **FedEx Data Repository**.

The original business-model and workflow implementation files are retained. The existing module manifest and model import registry are updated only to register the added files; those registrations are required for Odoo to load new models, views, data, and assets as one module.

Runtime installation against a live Odoo database is not performed by this archive build and should be validated on staging before production use.
