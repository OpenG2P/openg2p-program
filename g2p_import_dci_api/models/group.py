from odoo import fields, models


class OpenG2PGroup(models.Model):
    _inherit = "res.partner"

    grp_is_created_from_social_registry = fields.Boolean(
        "Imported from Social Registry", store=True
    )
