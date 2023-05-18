from odoo import fields, models


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    supporting_document_ids = fields.One2many("storage.file", "entitlement_id")
