from odoo import _, fields, models

from odoo.addons.g2p_programs.models import constants


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    show_payment_prepare = fields.Boolean(compute="_compute_show_payment_buttons")

    def _compute_show_payment_buttons(self):
        for rec in self:
            rec.show_payment_prepare = False
            payment_manager = self.program_id.get_manager(constants.MANAGER_PAYMENT)
            if (
                payment_manager
                and payment_manager._name == "g2p.program.payment.manager.cash"
                and rec.state in ("approved",)
                and rec.payment_status not in ("paid",)
            ):
                rec.show_payment_prepare = True

    def prepare_and_send_payment_cash(self):
        self.ensure_one()
        if self.state == "approved":
            payment_manager = self.program_id.get_manager(constants.MANAGER_PAYMENT)
            if (
                payment_manager
                and payment_manager._name == "g2p.program.payment.manager.cash"
            ):
                payments, batches = payment_manager._prepare_payments(
                    self.cycle_id, entitlements=self
                )
                payment_manager._send_payments(batches)
                kind = "success"
                message = _("Payment was issued and sent.")
            else:
                kind = "danger"
                message = _("Invalid operation!")
        else:
            kind = "danger"
            message = _("Entitlement is not approved!")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Payment"),
                "message": message,
                "sticky": True,
                "type": kind,
            },
        }
