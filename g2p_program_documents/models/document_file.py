from odoo import fields, models


class G2PDocument(models.Model):
    _inherit = "storage.file"

    program_membership_id = fields.Many2one("g2p.program_membership")

    entitlement_id = fields.Many2one("g2p.entitlement")
