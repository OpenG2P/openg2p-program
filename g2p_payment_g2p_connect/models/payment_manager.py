# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime, timedelta

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
    envelope_creation_url = fields.Char("Envelope Creation URL", required=True)
    envelope_status_url = fields.Char("Envelope Status URL", required=True)

    api_timeout = fields.Integer("API Timeout", default=10)

    payee_prefix = fields.Char(required=False, default=None)
    payee_suffix = fields.Char(required=False, default=None)

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

    def prepare_payments(self, cycle, entitlements=None):
        super().prepare_payments(cycle, entitlements)
        # Call Async Envelope in G2P Bridge only if cycle.disbursement_envelope_id is
        # not set and there are entitlements
        if not cycle.disbursement_envelope_id:
            self._create_envelope_g2p_bridge(cycle)
        return

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
        _logger.info(f"Total Batches:{len(batches)}")
        for batch in batches:
            _logger.info(f"Batch started:{batch.batch_has_started}")
            payee_fa = self._get_payee_fa(batch.payment_ids[0])
            _logger.info(f"Payee FA: {payee_fa}")
            if batch.batch_has_started:
                continue
            batch.batch_has_started = True
            batch_data = {
                "siganature": "string",
                "header": {
                    "version": "1.0.0",
                    "message_id": "string",
                    "message_ts": "string",
                    "action": "string",
                    "sender_id": "string",
                    "sender_uri": "",
                    "receiver_id": "",
                    "total_count": 0,
                    "is_msg_encrypted": False,
                    "meta": "string",
                },
                "message": [],
            }
            _logger.info(f"Total Payments{len(batch.payment_ids)}")

            for payment in batch.payment_ids:
                payee_fa = self._get_payee_fa(payment)
                if not payee_fa:
                    # TODO: Deal with no bank acc and/or ID type not matching any available IDs
                    payment.status = "failed"
                    continue
                _logger.info(f"Payee FA: {payee_fa}")
                batch_data["message"].append(
                    {
                        "disbursement_envelope_id": payment.disbursement_envelope_id,
                        "beneficiary_id": payee_fa,
                        "mis_reference_number": str(payment.id),
                        "beneficiary_name": payment.partner_id.name,
                        "disbursement_amount": payment.amount_issued,
                        "narrative": f"Payment for {batch.cycle_id.name} under {self.program_id.name}",
                    }
                )
            try:
                _logger.info("G2P Bridge Disbursement Batch Data: %s", batch_data)

                response = requests.post(
                    self.payment_endpoint_url,
                    json=batch_data,
                    timeout=self.api_timeout,
                )
                _logger.info("G2P Bridge Disbursement response: %s", response.content)
                response.raise_for_status()
                response = response.json()
                disbursements = response["message"]
                for disbursement in disbursements:
                    payment_by_ref = self.env["g2p.payment"].search(
                        [
                            ("disbursement_envelope_id", "=", disbursement["disbursement_envelope_id"]),
                            ("id", "=", disbursement["mis_reference_number"]),
                        ]
                    )
                    _logger.info(f"Payment by ref:{payment_by_ref}")
                    if payment_by_ref:
                        payment_by_ref.write(
                            {
                                "disbursement_id": disbursement["disbursement_id"],
                                "dispatch_status": "sent",
                                "amount_paid": disbursement["disbursement_amount"],
                            }
                        )

            except Exception as e:
                _logger.error("G2P Bridge Payment Failed with unknown reason: %s", str(e))
                error_msg = "G2P Bridge Payment Failed with unknown reason: " + str(e)
                self.message_post(body=error_msg, subject=_("G2P Bridge Payment Disbursement"))

    @api.model
    def payments_status_check(self, id_):
        payment_manager = self.browse(id_)
        batches = self.env["g2p.payment.batch"].search(
            [
                ("program_id", "=", payment_manager.program_id.id),
                ("stats_datetime", ">", datetime.now() - timedelta(days=3)),
            ]
        )

        _logger.info(f"Program id for Status Check: {payment_manager.program_id.id}")

        for batch in batches:
            _logger.info(f"Internal batch ref number:{batch.name}")

            payments = self.env["g2p.payment"].search(
                [
                    ("batch_id", "=", batch.id),
                    ("program_id", "=", payment_manager.program_id.id),
                    "|",
                    ("remittance_statement_id", "=", False),
                    ("reversal_statement_id", "=", False),
                ]
            )
            _logger.info("Total Payments for Status Check: %s", len(payments))
            for payment in payments:
                _logger.info(f"Payment for Status Check: {payment}")
                _logger.info(f"Payment Disbursement Id: {payment.disbursement_id}")

            _logger.info(f"Batch Id for Status Check: {batch.id}")
            _logger.info(f"Payment for Status Check: {len(payments)}")

            status_data = {
                "signature": "string",
                "header": {
                    "version": "1.0.0",
                    "message_id": "string",
                    "message_ts": "string",
                    "action": "string",
                    "sender_id": "string",
                    "sender_uri": "",
                    "receiver_id": "",
                    "total_count": 0,
                    "is_msg_encrypted": False,
                    "meta": "string",
                },
                "message": [str(payment.disbursement_id) for payment in payments],
            }
            try:
                _logger.info("G2P Connect Disbursement Status Data: %s", status_data)

                res = requests.post(
                    payment_manager.status_endpoint_url,
                    json=status_data,
                    timeout=payment_manager.api_timeout,
                )
                _logger.info("G2P Connect Disbursement Status response: %s", res.content)
                res.raise_for_status()
                res = res.json()
                res_list = res["message"]
                for res in res_list:
                    _logger.info(f"Disbursement ID inside Loop: {res['disbursement_id']}")
                    payment_by_ref = self.env["g2p.payment"].search(
                        [("disbursement_id", "=", res["disbursement_id"])]
                    )
                    for recon in res["disbursement_recon_records"].get("disbursement_recon_payloads"):
                        payment_by_ref.write(
                            {
                                "remittance_reference_number": recon["remittance_reference_number"],
                                "remittance_statement_id": recon["remittance_statement_id"],
                                "remittance_entry_sequence": recon["remittance_entry_sequence"],
                                "remittance_entry_date": recon["remittance_entry_date"],
                                "reversal_statement_id": recon["reversal_statement_id"],
                                "reversal_entry_sequence": recon["reversal_entry_sequence"],
                                "reversal_entry_date": recon["reversal_entry_date"],
                                "reversal_reason": recon["reversal_reason"],
                            }
                        )

            except Exception as e:
                _logger.exception(
                    "G2P Connect Disbursement Status Check Failed with unknown reason. %s",
                    str(e),
                )
                error_msg = "G2P Connect Status Check Failed with unknown reason: " + str(e)
                payment_manager.message_post(body=error_msg, subject=_("G2P Connect Status Check"))

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
                    return (
                        f"{self.payee_prefix if self.payee_prefix else ''}"
                        f"{reg_id.value}{self.payee_suffix if self.payee_suffix else ''}"
                    )
        return None

    @api.model
    def get_registrant_or_group_head(self, partner):
        partner.ensure_one()
        head_membership = self.env.ref("g2p_registry_membership.group_membership_kind_head")
        if partner.is_group:
            partner = partner.group_membership_ids.filtered(lambda x: head_membership in x.kind)
            partner = partner[0].individual if partner else None
            _logger.info(f"Partner is:{partner}")
        return partner

    def stop_status_check_cron(self):
        for rec in self:
            if rec.status_check_cron_id:
                rec.status_check_cron_id.unlink()

    def _create_envelope_g2p_bridge(self, cycle):
        _logger.info("Creating envelope for g2p_bridge")
        total_no_of_payments_across_batches = cycle.program_id.eligible_beneficiaries_count
        total_payment_amount = cycle.total_amount
        program_name = cycle.program_id.name
        currency_code = cycle.program_id.company_id.currency_id.name
        disbursement_schedule_date = cycle.start_date
        # frequency = self.cycle_duration
        envelope_request_data = {
            "signature": "string",
            "header": {
                "version": "1.0.0",
                "message_id": "string",
                "message_ts": "string",
                "action": "string",
                "sender_id": "string",
                "sender_uri": "",
                "receiver_id": "",
                "total_count": 0,
                "is_msg_encrypted": False,
                "meta": "string",
            },
            "message": {
                "benefit_program_mnemonic": program_name,
                "disbursement_frequency": "OnDemand",  # TODO
                "cycle_code_mnemonic": "SEP",  # TODO
                "number_of_beneficiaries": total_no_of_payments_across_batches,
                "number_of_disbursements": total_no_of_payments_across_batches,
                "total_disbursement_amount": total_payment_amount,
                "disbursement_currency_code": currency_code,
                "disbursement_schedule_date": str(disbursement_schedule_date),
            },
        }
        try:
            response = requests.post(
                self.envelope_creation_url,
                json=envelope_request_data,
                timeout=10,
            )
            # Store the id from respose to the model
            disbursement_envelope_id = response.json().get("message").get("disbursement_envelope_id")
            cycle.write({"disbursement_envelope_id": disbursement_envelope_id})
            _logger.info(f"G2P Connect Disbursement Envelope response:{response.content}")
            response.raise_for_status()
            return True
        except Exception as e:
            _logger.error(f"G2P Connect Disbursement Envelope Failed with reason:{str(e)}")
        return False

        # Not being used right now, bridge enveleope is created synchronously

    def _create_envelope_g2p_bridge_async(self, cycle):
        _logger.info("Creating Envelope in Async mode")
        cycle.message_post(body=_("Creating the envelope for the cycle."))
        cycle.write(
            {
                "locked": True,
                "locked_reason": _("Creating the envelope for the cycle."),
            }
        )

        jobs = [
            self.delayable()._create_envelope_g2p_bridge(cycle),
        ]
        main_job = group(*jobs)
        main_job.on_done(self.delayable().mark_job_as_done(cycle, _("Created envelope.")))
        main_job.delay()
