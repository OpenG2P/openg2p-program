# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
import uuid
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
        "g2p.program.payment.manager.file",
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
    reg_id_type_for_payee_id = fields.Many2one("g2p.id.type", "Payee DFSP ID Type", required=False)
    payment_endpoint_url = fields.Char("Payment Endpoint URL", required=True)
    status_endpoint_url = fields.Char("Status Endpoint URL", required=True)

    api_timeout = fields.Integer("API Timeout", default=10)

    payee_prefix = fields.Char()
    payee_suffix = fields.Char()

    locale = fields.Char(required=True)

    status_check_cron_id = fields.Many2one(
        "ir.cron",
        string="Cron Job",
        help="linked to this Payment connector",
        required=False,
    )
    status_check_cron_active = fields.Boolean(
        related="status_check_cron_id.active",
    )
    status_cron_job_interval_minutes = fields.Integer(default=1)

    payment_file_config_ids = fields.Many2many(
        "g2p.payment.file.config", "g2p_pay_file_config_pay_manager_g2pconnect"
    )
    send_payments_domain = fields.Text("Filter Batches to Send", default="[]")

    @api.onchange("payee_id_type")
    def _onchange_payee_id_type(self):
        prefix_mapping = {
            "bank_acc_no": "account_no:",
            "bank_acc_iban": "iban:",
            "phone": "phone:",
            "email": "email:",
            # TODO: Need to add key:value pair for reg_id
        }
        self.payee_prefix = prefix_mapping.get(self.payee_id_type)

    def _send_payments(self, batches):
        if batches:
            batches = batches.filtered_domain(self._safe_eval(self.send_payments_domain))
        if not self.status_check_cron_id:
            self.status_check_cron_id = (
                self.env["ir.cron"]
                .sudo()
                .create(
                    {
                        "name": "G2P Connect Payment Manager Status Cron " + self.name + " #" + str(self.id),
                        "active": True,
                        "interval_number": self.status_cron_job_interval_minutes,
                        "interval_type": "minutes",
                        "model_id": self.env["ir.model"].search([("model", "=", self._name)]).id,
                        "state": "code",
                        "code": "model.payments_status_check(" + str(self.id) + ")",
                        "doall": False,
                        "numbercall": -1,
                    }
                )
            )
        _logger.info("DEBUG! send_payments Manager: G2P Connect.")
        for batch in batches:
            if batch.batch_has_started:
                continue
            batch.batch_has_started = True
            batch_data = {
                "signature": 'Signature: namespace="g2p", kidId="{sender_id}|{unique_key_id}|{algorithm}", '
                'algorithm="ed25519", created="1606970629", expires="1607030629", '
                'headers="(created) (expires) digest", signature="Base64(signing content)',
                "header": {
                    "message_id": str(uuid.uuid4()),
                    "message_ts": str(datetime.utcnow()),
                    "action": "disburse",
                    "sender_id": "payments.openg2p.org",
                    "receiver_id": "pymts.example.org",
                    "total_count": len(batch.payment_ids),
                },
                "message": {"transaction_id": batch.name, "disbursements": []},
            }
            for payment in batch.payment_ids:
                batch_data["message"]["disbursements"].append(
                    {
                        "reference_id": payment.name,
                        "payer_fa": "",
                        "payee_fa": self._get_payee_fa(payment),
                        "amount": str(payment.amount_issued),
                        "payee_name": payment.partner_id.name,
                        "note": f"Payment for {batch.cycle_id.name} under {self.program_id.name}",
                        "scheduled_timestamp": str(datetime.utcnow()),
                        "purpose": self.program_id.name,
                        "currency_code": payment.currency_id.name,
                        "locale": self.locale,
                    }
                )
            try:
                response = requests.post(
                    self.payment_endpoint_url,
                    json=batch_data,
                    timeout=self.api_timeout,
                )
                _logger.info("G2P Connect Disbursement response: %s", response.content)
                response.raise_for_status()

            except Exception as e:
                _logger.error("G2P Connect Payment Failed with unknown reason: %s", str(e))
                error_msg = "G2P Connect Payment Failed with unknown reason: " + str(e)
                self.message_post(body=error_msg, subject=_("G2P Connect Payment Disbursement"))

    @api.model
    def payments_status_check(self, id_):
        payment_manager = self.browse(id_)
        payments = self.env["g2p.payment"].search(
            [("program_id", "=", payment_manager.program_id.id), ("status", "=", None)]
        )
        status_data = {
            "signature": 'Signature: namespace="g2p", kidId="{sender_id}|{unique_key_id}|{algorithm}", '
            'algorithm="ed25519", created="1606970629", expires="1607030629", '
            'headers="(created) (expires) digest", signature="Base64(signing content)',
            "header": {
                "message_id": str(uuid.uuid4()),
                "message_ts": str(datetime.utcnow()),
                "action": "disburse",
                "sender_id": "payments.openg2p.org",
                "receiver_id": "pymts.example.org",
                "total_count": len(payments),
            },
            "message": {
                "transaction_id": str(uuid.uuid4()),
                "txnstatus_request": {
                    "reference_id": str(uuid.uuid4()),
                    "txn_type": "disburse",
                    "attribute_type": "reference_id_list",
                    "attribute_value": [str(payment.name) for payment in payments],
                    "locale": "eng",
                },
            },
        }
        try:
            res = requests.post(
                payment_manager.status_endpoint_url,
                json=status_data,
                timeout=payment_manager.api_timeout,
            )
            _logger.info("G2P Connect Disbursement Status response: %s", res.content)
            res.raise_for_status()
            res = res.json()
            res_list = res["message"]["txnstatus_response"]["txn_status"]
            for res in res_list:
                if res:
                    payments_by_ref = self.env["g2p.payment"].search([("name", "=", res["reference_id"])])
                    if res["status"] == "succ":
                        payments_by_ref.state = "reconciled"
                        payments_by_ref.status = "paid"
                    elif res["status"] == "rjct":
                        payments_by_ref.state = "reconciled"
                        payments_by_ref.status = "failed"

        except Exception as e:
            _logger.exception(
                "G2P Connect Disbursement Status Check Failed with unknown reason. %s",
                str(e),
            )
            error_msg = "G2P Connect Status Check Failed with unknown reason: " + str(e)
            payment_manager.message_post(body=error_msg, subject=_("G2P Connect Status Check"))

        batches = self.env["g2p.payment.batch"].search(
            [
                ("program_id", "=", payment_manager.program_id.id),
                ("batch_has_started", "=", True),
                ("batch_has_completed", "=", False),
            ]
        )
        if not batches:
            # If there are no batches like this .. the cron will be deleted
            payment_manager.sudo().with_delay().stop_status_check_cron()
        for batch in batches:
            no_payments_left = len(batch.payment_ids.filtered(lambda x: x.status not in ("paid", "failed")))
            if no_payments_left == 0:
                batch.batch_has_completed = True

    def stop_status_check_cron(self):
        for rec in self:
            rec.status_check_cron_id.unlink()
            rec.status_check_cron_id = None

    def _get_payee_fa(self, payment):
        self.ensure_one()
        partner = self.get_registrant_or_group_head(payment.partner_id)
        if not partner:
            return None

        payee_id_type = self.payee_id_type
        if payee_id_type == "bank_acc_no":
            # TODO: Compute which bank_acc_no to choose from bank account list
            for bank_id in partner.bank_ids:
                return f"{self.payee_prefix}{bank_id.acc_number}@{bank_id.bank_id.bic}"
        elif payee_id_type == "bank_acc_iban":
            # TODO: Compute which iban to choose from bank account list
            for bank_id in partner.bank_ids:
                return f"{self.payee_prefix}{bank_id.iban}@{bank_id.bank_id.bic}"
        elif payee_id_type == "phone":
            return f"{self.payee_prefix}{partner.phone}"
        elif payee_id_type == "email":
            return f"{self.payee_prefix}{partner.email}"
        elif payee_id_type == "reg_id":
            for reg_id in partner.reg_ids:
                if reg_id.id_type.id == self.reg_id_type_for_payee_id.id:
                    return f"{self.payee_prefix}{reg_id.value}{self.payee_suffix}"
        # TODO: Deal with no bank acc and/or ID type not matching any available IDs
        return None

    @api.model
    def get_registrant_or_group_head(self, partner):
        partner.ensure_one()
        head_membership = self.env.ref("g2p_registry_membership.group_membership_kind_head")
        if partner.is_group:
            partner = partner.group_membership_ids.filtered(lambda x: head_membership in x.kind)
            partner = partner[0].individual if partner else None
        return partner
