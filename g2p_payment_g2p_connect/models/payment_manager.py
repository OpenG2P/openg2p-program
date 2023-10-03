# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime

import requests

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.g2p.connect",
            "G2P Connect Payment Manager",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PPaymentManagerG2PConnect(models.Model):
    _name = "g2p.program.payment.manager.g2p.connect"
    _inherit = [
        "g2p.program.payment.manager.default",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _description = "G2P Connect Payment Manager"

    batch_tag_ids = fields.Many2many(
        "g2p.payment.batch.tag",
        "g2p_pay_batch_tag_pay_manager_g2p_connect",
        string="Batch Tags",
        ondelete="cascade",
    )
    create_batch = fields.Boolean("Automatically Create Batch", default=True)
    payee_id_type = fields.Selection(
        [
            ("bank_acc_no", "Bank Account Number"),
            ("bank_acc_iban", "IBAN"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("reg_id", "Registrant ID"),
        ],
        "Payee ID Field",
        required=True,
    )
    reg_id_type_for_payee_id = fields.Many2one(
        "g2p.id.type", "Payee DFSP ID Type", required=False
    )
    payment_endpoint_url = fields.Char("Payment Endpoint URL", required=True)

    api_timeout = fields.Integer("API Timeout", default=10)

    username = fields.Char(required=True)
    password = fields.Char(required=True)

    payer_fa = fields.Char(string="Payer Financial Address", required=True)
    payer_name = fields.Char(required=True)
    locale = fields.Char(required=True)

    def _send_payments(self, batches):
        _logger.info("DEBUG! send_payments Manager: G2P Connect.")
        for batch in batches:
            if batch.batch_has_started:
                continue
            batch.batch_has_started = True
            batch_data = {
                "signature": 'Signature: namespace="g2p", kidId="{sender_id}|{unique_key_id}|{algorithm}", algorithm="ed25519", created="1606970629", expires="1607030629", headers="(created) (expires) digest", signature="Base64(signing content)',
                "header": {
                    "version": "1.0.0",
                    "message_id": "123",
                    "message_ts": "",
                    "action": "search",
                    "sender_id": "spp.example.org",
                    "sender_uri": "https://spp.example.org/{namespace}/callback/on-search",
                    "receiver_id": "pymts.example.org",
                    "total_count": 21800,
                    "is_msg_encrypted": False,
                    "meta": {},
                },
                "message": {"transaction_id": batch.name, "disbursements": []},
            }
            headers = {
                "Content-Type": "application/json",
            }
            for payment in batch.payment_ids:
                batch_data["message"]["disbursements"].append(
                    {
                        "reference_id": payment.name,
                        "payer_fa": self.payer_fa,
                        "payee_fa": self._get_payee_fa(payment),
                        "amount": payment.amount_issued,
                        "scheduled_timestamp": "",
                        "payer_name": self.payer_name,
                        "payee_name": payment.partner_id.name,
                        "note": "string",
                        "purpose": self.program_id.name,
                        "instruction": "string",
                        "currency_code": payment.currency_id.name,
                        "locale": self.locale,
                    }
                )
            try:
                response = requests.post(
                    self.payment_endpoint_url, json=batch_data, headers=headers
                )
                _logger.info("G2P Connect Disbursement response: %s", response.content)
                response.raise_for_status()

                # TODO: Do Status check rather than hardcoding
                for payment in batch.payment_ids:
                    payment.state = "sent"
                    payment.status = "paid"
                    payment.amount_paid = payment.amount_issued
                    payment.payment_datetime = datetime.utcnow()

            except Exception as e:
                _logger.error(
                    "G2P Connect Payment Failed with unknown reason: %s", str(e)
                )
                error_msg = "G2P Connect Payment Failed with unknown reason: " + str(e)
                self.message_post(
                    body=error_msg, subject=_("G2P Connect Payment Disbursement")
                )

            # TODO: Compute status of disbursement from API
            batch.batch_has_completed = True

    def _get_payee_fa(self, payment):
        self.ensure_one()
        payee_id_type = self.payee_id_type
        if payee_id_type == "bank_acc_no":
            # TODO: Compute which bank_acc_no to choose from bank account list
            for bank_id in payment.partner_id.bank_ids:
                return bank_id.acc_number
        elif payee_id_type == "bank_acc_iban":
            # TODO: Compute which iban to choose from bank account list
            for bank_id in payment.partner_id.bank_ids:
                return bank_id.iban
        elif payee_id_type == "phone":
            return payment.partner_id.phone
        elif payee_id_type == "email":
            return payment.partner_id.email
        elif payee_id_type == "reg_id":
            for reg_id in payment.partner_id.reg_ids:
                if reg_id.id_type.id == self.reg_id_type_for_payee_id.id:
                    return reg_id.value
        # TODO: Deal with no bank acc and/or ID type not matching any available IDs
        return None
