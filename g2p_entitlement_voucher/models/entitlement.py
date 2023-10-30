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

    show_generate_voucher_button = fields.Boolean(
        compute="_compute_show_voucher_buttons"
    )
    show_print_voucher_button = fields.Boolean(compute="_compute_show_voucher_buttons")

    def _compute_show_voucher_buttons(self):
        for rec in self:
            rec.show_generate_voucher_button = False
            rec.show_print_voucher_button = False
            entitlement_manager = self.program_id.get_manager(
                constants.MANAGER_ENTITLEMENT
            )
            if rec.state in ("approved",):
                if (
                    entitlement_manager
                    and entitlement_manager._name
                    == "g2p.program.entitlement.manager.voucher"
                    and not rec.voucher_document_id
                ):
                    rec.show_generate_voucher_button = True
                if rec.voucher_document_id:
                    rec.show_print_voucher_button = True

    def generate_vouchers_action(self):
        err, message, sticky, vouchers = self.program_id.get_manager(
            constants.MANAGER_ENTITLEMENT
        ).generate_vouchers(self)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Voucher"),
                "message": message,
                "sticky": sticky,
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
