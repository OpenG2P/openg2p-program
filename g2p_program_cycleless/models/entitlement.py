from odoo import fields, models


class G2PPrograms(models.Model):
    _inherit = "g2p.entitlement"

    vendor_id = fields.Many2one("res.partner", String="Service Provider")
