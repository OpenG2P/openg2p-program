# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.simple.mpesa",
            "Simple MPesa Payment Manager",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PPaymentManagerSimpleMpesa(models.Model):
    _name = "g2p.program.payment.manager.simple.mpesa"
    _inherit = "g2p.program.payment.manager.default"
    _description = "Simple MPesa Payment Manager"

    batch_tag_ids = fields.Many2many(
        "g2p.payment.batch.tag",
        "g2p_pay_batch_tag_pay_manager_simple_mpesa",
        string="Batch Tags",
        ondelete="cascade",
    )

    create_batch = fields.Boolean("Automatically Create Batch", default=True)

    auth_endpoint_url = fields.Char("Authentication Endpoint URL", required=True)
    payment_endpoint_url = fields.Char("Payment Endpoint URL", required=True)

    username = fields.Char(required=True)
    password = fields.Char(required=True)

    def _send_payments(self, batches):
        # Transfer to Simple Mpesa
        _logger.info("DEBUG! send_payments Manager: Simple Mpesa.")
        for batch in batches:
            if batch.batch_has_started:
                continue
            else:
                batch.batch_has_started = True

            # TODO: Implement Logic

            batch.payment_ids.write({"state": "sent"})
