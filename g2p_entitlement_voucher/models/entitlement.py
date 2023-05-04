from odoo import fields, models


class G2PPaymentFileQRCode(models.TransientModel):
    _inherit = "g2p.payment.file.qrcode"

    entitlement_id = fields.Many2one("g2p.entitlement")


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    # this is never to be accessed outside template rendering
    qrcode_ids = fields.One2many("g2p.payment.file.qrcode", "entitlement_id")

    voucher_document_id = fields.Many2one("storage.file")
