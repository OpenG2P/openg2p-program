from odoo import fields, models


class OdkConfig(models.Model):
    _inherit = "odk.import"

    program = fields.Many2one("g2p.program", domain="[('target_type', '=', target_registry)]")
