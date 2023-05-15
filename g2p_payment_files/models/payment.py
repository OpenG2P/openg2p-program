from odoo import fields, models


class G2PPayment(models.Model):
    _inherit = "g2p.payment"

    qrcode_ids = fields.One2many("g2p.payment.file.qrcode", "payment_id")

    payment_file_ids = fields.Many2many("storage.file")


class G2PPaymentBatch(models.Model):
    _inherit = "g2p.payment.batch"

    qrcode_ids = fields.One2many("g2p.payment.file.qrcode", "payment_batch_id")

    payment_file_ids = fields.Many2many("storage.file")
