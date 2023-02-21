# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime

import requests
from requests.exceptions import HTTPError

from odoo import api, fields, models

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

    use_iban_for_payee_id = fields.Boolean(
        "Use IBAN for Payee DFSP ID Value?", required=False
    )
    id_for_payee_id = fields.Many2one(
        "g2p.id.type", "Payee DFSP ID Type", required=False
    )

    # TODO: Splits Payments into smalelr batches rather than One whole batch

    def send_payments(self, batches):
        payment_endpoint_url = self.payment_endpoint_url
        _logger.info(
            f"DEBUG! send_payments Manager: Payment Interop Layer - URL: {payment_endpoint_url}"
        )
        for batch in batches:
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
                # TODO: The following is to be called during payment preperation not during sending
                payee_id_type, payee_id_value = self._get_dfsp_id_and_type(payment_id)
                payee_item = {
                    "payeeIdType": payee_id_type,
                    "payeeIdValue": payee_id_value,
                    "amount": payment_id.amount_issued,
                    "currency": payment_id.currency_id.name,
                }
                final_json_request_dict["payeeList"].append(payee_item)

            # TODO: Add authentication mechanism
            try:
                res = requests.post(payment_endpoint_url, json=final_json_request_dict)
                res.raise_for_status()
                # TODO: Perform detailed parsing of jsonResponse
                # access JSOn content
                jsonResponse = res.json()
                _logger.info(
                    f"Interop Layer Disbursement API: jsonResponse: {jsonResponse}"
                )

            except HTTPError as http_err:
                _logger.error(
                    f"Interop Layer Disbursement API: HTTP error occurred: {http_err}. res: {res} - {res.content}"
                )
                continue
            except Exception as err:
                _logger.error(
                    f"Interop Layer Disbursement API: Other error occurred: {err}. res: {res} - {res.content}"
                )
                continue

            # TODO: reconcile and update each payment status properly
            paid_counter = 0
            for i, payee_result in enumerate(jsonResponse["payeeResults"]):
                if payee_result["status"] == "COMPLETED":
                    paid_counter += 1
                    batch.payment_ids[i].update(
                        {
                            "state": "sent",
                            "amount_paid": payee_result["amountCredited"],
                            "payment_datetime": datetime.strptime(
                                payee_result["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
                            ),
                        }
                    )
            if paid_counter and paid_counter == len(batch.payment_ids):
                batch.batch_has_completed = True

    def _get_dfsp_id_and_type(self, payment):
        self.ensure_one()
        if self.use_iban_for_payee_id:
            # TODO: Compute which IBAN to choose from bank account list
            for bank_id in payment.partner_id.bank_ids:
                return "IBAN", bank_id.iban
        else:
            for reg_id in payment.partner_id.reg_ids:
                if reg_id.id_type == self.id_for_payee_id:
                    return self.id_for_payee_id.name, reg_id.value
        # TODO: Deal with no bank acc and/or ID type not matching any available IDs
        return None, None
