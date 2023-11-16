# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime

import requests
from requests.exceptions import HTTPError

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.payment.interop.layer",
            "Payment Interoperability Layer",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PPaymentInteropLayerManager(models.Model):
    _name = "g2p.program.payment.manager.payment.interop.layer"
    _inherit = "g2p.program.payment.manager.default"
    _description = "Payment Interoperability Layer"

    payment_endpoint_url = fields.Char("Payment Endpoint URL", required=True)

    # The following urls are not used at the moment
    # status_endpoint_url = fields.Char("Status Endpoint URL", required=True)
    # details_endpoint_url = fields.Char("Details Endpoint URL", required=True)

    create_batch = fields.Boolean("Automatically Create Batch", default=True)

    batch_tag_ids = fields.Many2many(
        "g2p.payment.batch.tag",
        "g2p_pay_batch_tag_pay_manager_interop_layer",
        string="Batch Tags",
        ondelete="cascade",
    )

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

    payee_id_type_to_send = fields.Char(
        default="ACCOUNT_ID", help="This will be replaced for the payee ID type"
    )

    def _send_payments(self, batches):
        payment_endpoint_url = self.payment_endpoint_url
        all_paid_counter = 0
        if not batches:
            message = _("No payment batches to process.")
            kind = "warning"
        else:
            for batch in batches:
                if batch.batch_has_started:
                    continue
                else:
                    batch.batch_has_started = True

                disbursement_id = batch.name

                cycle_id = batch.cycle_id
                disbursement_note = (
                    f"Program: {cycle_id.program_id.name}. Cycle ID - {cycle_id.name}"
                )

                final_json_request_dict = {
                    "note": disbursement_note,
                    "disbursementId": disbursement_id,
                    "payeeList": [],
                }

                for payment_id in batch.payment_ids:
                    payee_id_type, payee_id_value = self._get_dfsp_id_and_type(
                        payment_id
                    )
                    payee_item = {
                        "payeeIdType": payee_id_type,
                        "payeeIdValue": payee_id_value,
                        "amount": payment_id.amount_issued,
                        "currency": payment_id.currency_id.name,
                    }
                    final_json_request_dict["payeeList"].append(payee_item)

                # TODO: Add authentication mechanism
                res = None
                try:
                    res = requests.post(
                        payment_endpoint_url, json=final_json_request_dict
                    )
                    res.raise_for_status()
                    jsonResponse = res.json()
                    _logger.info(
                        f"Interop Layer Disbursement API: jsonResponse: {jsonResponse}"
                    )

                except HTTPError as http_err:
                    if res is not None:
                        _logger.error(
                            "Interop Layer Disbursement API: HTTP error occurred: "
                            f"{http_err}. res: {res} - {res.content}"
                        )

                    else:
                        _logger.error(
                            f"Interop Layer Disbursement API: HTTP error occurred: {http_err}."
                        )
                    continue

                except Exception as err:
                    if res is not None:
                        _logger.error(
                            f"Interop Layer Disbursement API: Other error occurred: {err}. res: {res} - {res.content}"
                        )
                    else:
                        _logger.error(
                            f"Interop Layer Disbursement API: Other error occurred: {err}."
                        )
                    continue

                batch.payment_ids.write({"state": "sent"})

                paid_counter = 0
                for i, payee_result in enumerate(jsonResponse["payeeResults"]):
                    if payee_result["status"] == "COMPLETED":
                        paid_counter += 1
                        batch.payment_ids[i].update(
                            {
                                "state": "reconciled",
                                "status": "paid",
                                "amount_paid": payee_result["amountCredited"],
                                "payment_datetime": datetime.strptime(
                                    payee_result["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
                                ),
                            }
                        )
                    elif payee_result["status"] in [
                        "REJECTED",
                        "ABORTED",
                        "ERROR_OCCURRED",
                    ]:
                        batch.payment_ids[i].update(
                            {
                                "state": "reconciled",
                                "status": "failed",
                            }
                        )
                if paid_counter and paid_counter == len(batch.payment_ids):
                    batch.batch_has_completed = True
                all_paid_counter += paid_counter

            total_payments_counter = sum(len(batch.payment_ids) for batch in batches)
            if all_paid_counter == total_payments_counter:
                message = _(f"{all_paid_counter} Payments sent successfully")
                kind = "success"
            elif all_paid_counter == 0:
                message = _("Failed to sent payments")
                kind = "danger"
            else:
                message = _(
                    f"{all_paid_counter} Payments sent successfully out of {total_payments_counter}"
                )
                kind = "warning"

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

    def _get_dfsp_id_and_type(self, payment):
        self.ensure_one()
        payee_id_type = self.payee_id_type
        payee_id_type_to_send = self.payee_id_type_to_send
        if payee_id_type == "bank_acc_no":
            if not payee_id_type_to_send:
                payee_id_type_to_send = "ACCOUNT_ID"

            # TODO: Compute which bank_acc_no to choose from bank account list
            for bank_id in payment.partner_id.bank_ids:
                return payee_id_type_to_send, bank_id.acc_number
        elif payee_id_type == "bank_acc_iban":
            if not payee_id_type_to_send:
                payee_id_type_to_send = "IBAN"

            # TODO: Compute which iban to choose from bank account list
            for bank_id in payment.partner_id.bank_ids:
                return payee_id_type_to_send, bank_id.iban
        elif payee_id_type == "phone":
            if not payee_id_type_to_send:
                payee_id_type_to_send = "PHONE"

            return payee_id_type_to_send, payment.partner_id.phone
        elif payee_id_type == "email":
            if not payee_id_type_to_send:
                payee_id_type_to_send = "EMAIL"

            return payee_id_type_to_send, payment.partner_id.email
        elif payee_id_type == "reg_id":
            if not payee_id_type_to_send:
                payee_id_type_to_send = self.reg_id_type_for_payee_id.name

            for reg_id in payment.partner_id.reg_ids:
                if reg_id.id_type.id == self.reg_id_type_for_payee_id.id:
                    return payee_id_type_to_send, reg_id.value
        # TODO: Deal with no bank acc and/or ID type not matching any available IDs
        return None, None
