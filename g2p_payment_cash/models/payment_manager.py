# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.cash",
            "Cash Payment Manager",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PCryptoKeySet(models.Model):
    _inherit = "g2p.crypto.key.set"

    cash_payment_manager_id = fields.Many2one(
        "g2p.program.payment.manager.cash", ondelete="cascade"
    )


class G2PPaymentManagerCash(models.Model):
    _name = "g2p.program.payment.manager.cash"
    _inherit = "g2p.program.payment.manager.file"
    _description = "Cash Payment Manager"

    batch_tag_ids = fields.Many2many(
        "g2p.payment.batch.tag",
        "g2p_pay_batch_tag_pay_manager_cash",
        string="Batch Tags",
        ondelete="cascade",
    )

    # This is a one2one relation
    crypto_key_set = fields.One2many("g2p.crypto.key.set", "cash_payment_manager_id")

    # This will just mark all the payments as done when then cash is given out
    def _send_payments(self, batches):
        _logger.info("DEBUG! send_payments Manager: Payment via CASH")
        for batch in batches:
            batch.batch_has_started = True
            for payment in batch.payment_ids:
                payment.update(
                    {
                        "state": "reconciled",
                        "status": "paid",
                        "amount_paid": payment.amount_issued,
                        "payment_datetime": datetime.utcnow(),
                    }
                )
            batch.batch_has_completed = True

        message = _("Payment files created successfully")
        kind = "success"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Payment"),
                "message": message,
                "sticky": True,
                "type": kind,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }
