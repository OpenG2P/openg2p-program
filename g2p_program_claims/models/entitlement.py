from odoo import fields, models


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    vendor_id = fields.Many2one("res.partner")

    claim_original_entitlement_id = fields.Many2one(
        "g2p.entitlement", string="Original Entitlement of this Claim"
    )

    claim_entitlement_ids = fields.One2many(
        "g2p.entitlement", "claim_original_entitlement_id"
    )
