from odoo import _, fields, models

from odoo.addons.g2p_programs.models import constants


class G2PPaymentFileQRCode(models.TransientModel):
    _inherit = "g2p.payment.file.qrcode"

    entitlement_id = fields.Many2one("g2p.entitlement")


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    # this is never to be accessed outside template rendering
    qrcode_ids = fields.One2many("g2p.payment.file.qrcode", "entitlement_id")

    voucher_document_id = fields.Many2one("storage.file")

    def generate_vouchers_action(self):
        err, message, vouchers = self.program_id.get_manager(
            constants.MANAGER_ENTITLEMENT
        ).generate_vouchers(self)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Voucher"),
                "message": message,
                "sticky": True,
                "type": "success",
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }

    def print_voucher_action(self):
        if self.voucher_document_id:
            return {
                "type": "ir.actions.act_url",
                "name": _("Voucher"),
                "target": "new",
                "url": self.voucher_document_id.url,
            }
