# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import base64
import csv
import logging
from io import StringIO
from uuid import uuid4

import requests
from requests.exceptions import HTTPError

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = ("g2p.program.payment.manager.phee", "Payment Hub EE")
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PPaymentHubEEManager(models.Model):
    _name = "g2p.program.payment.manager.phee"
    _inherit = [
        "g2p.base.program.payment.manager",
        "g2p.manager.source.mixin",
    ]
    _description = "Payment Hub EE Payment Manager"

    create_batch = fields.Boolean("Automatically Create Batch")
    max_batch_size = fields.Integer(default=500)

    auth_endpoint_url = fields.Char("Authentication Endpoint URL", required=True)
    payment_endpoint_url = fields.Char("Payment Endpoint URL", required=True)
    status_endpoint_url = fields.Char("Status Endpoint URL", required=True)
    details_endpoint_url = fields.Char("Details Endpoint URL", required=True)

    # Authentication parameters
    tenant_id = fields.Char("Tenant ID", required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    grant_type = fields.Char(required=True)
    authorization = fields.Char(required=True)

    # Authentication token storage
    auth_token = fields.Char("Authentication Token", help="A JWT")

    payment_mode = fields.Char(required=True)

    payer_id_type = fields.Char(required=True)
    payer_id = fields.Char(required=True)

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

    # Payment parameters
    file_name_prefix = fields.Char("Filename Prefix", default="ph_ee_")
    batch_type_header = fields.Char("Batch Transaction Type Header", default="type")
    batch_purpose_header = fields.Char(
        "Batch Transaction Purpose Header", default="G2P Payment"
    )
    batch_request_timeout = fields.Integer(
        help="Batch request timeout in seconds", default=10
    )

    make_csv_at_prepare = fields.Boolean(
        help="Make CSV files as attachemnts during Preparation"
    )

    # TODO: optimize code to do in a single query.
    def prepare_payments(self, cycle):
        entitlements = cycle.entitlement_ids.filtered(lambda a: a.state == "approved")
        if entitlements:
            entitlements_ids = entitlements.ids

            # Filter out entitlements without payments
            entitlements_with_payments = (
                self.env["g2p.payment"]
                .search(
                    [
                        ("entitlement_id", "in", entitlements_ids),
                        "!",
                        "&",
                        ("state", "=", "reconciled"),
                        ("status", "=", "failed"),
                    ]
                )
                .mapped("entitlement_id.id")
            )
            entitlements_to_pay = list(
                set(entitlements_ids) - set(entitlements_with_payments)
            )

            if not entitlements_to_pay:
                return cycle.mark_distributed()

            entitlements_to_pay = self.env["g2p.entitlement"].browse(
                entitlements_to_pay
            )

            max_batch_size = self.max_batch_size
            is_create_batch = self.create_batch

            payments = []
            curr_batch = None
            for i, entitlement_id in enumerate(entitlements_to_pay):
                each_payment = self.env["g2p.payment"].create(
                    {
                        "name": str(uuid4()),
                        "entitlement_id": entitlement_id.id,
                        "cycle_id": entitlement_id.cycle_id.id,
                        "amount_issued": entitlement_id.initial_amount,
                        "payment_fee": entitlement_id.transfer_fee,
                        "state": "issued",
                    }
                )
                payments.append(each_payment)
                if is_create_batch:
                    if i % max_batch_size == 0:
                        curr_batch = self.env["g2p.payment.batch"].create(
                            {
                                "name": str(uuid4()),
                                "cycle_id": cycle.id,
                                "stats_datetime": fields.Datetime.now(),
                            }
                        )
                    curr_batch.payment_ids = [(4, each_payment.id)]
                    each_payment.batch_id = curr_batch

                    if self.make_csv_at_prepare and (
                        i % max_batch_size == max_batch_size - 1
                        or i == len(entitlements_to_pay) - 1
                    ):
                        data = self.prepare_csv_for_batch(curr_batch)
                        csv_data_bin = data.getvalue().encode()
                        filename = f"{self.file_name_prefix}{curr_batch.name}.csv"
                        self.create_update_csv_attachment(filename, csv_data_bin)
            if payments:
                kind = "success"
                message = _("%s new payments was issued.", len(payments))
                links = [
                    {
                        "label": "Refresh Page",
                    }
                ]
                refresh = " %s"
            else:
                kind = "danger"
                message = _("There are no new payments issued!")
                links = []
                refresh = ""
        else:
            kind = "danger"
            message = _("All entitlements selected are not approved!")
            links = []
            refresh = ""

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Payment Hub EE"),
                "message": message + refresh,
                "links": links,
                "sticky": True,
                "type": kind,
            },
        }

    def send_payments(self, batches):
        # Bulk Transfer to PHEE API
        payment_endpoint_url = self.payment_endpoint_url
        tenant_id = self.tenant_id
        _logger.info(
            f"DEBUG! send_payments Manager: PHEE - URL: {payment_endpoint_url} tenant: {tenant_id}"
        )
        batch_request_timeout = self.batch_request_timeout
        for batch in batches:
            if batch.batch_has_started:
                continue

            x_correlation_id = str(uuid4())
            batch.external_batch_ref = x_correlation_id

            filename = f"{self.file_name_prefix}{batch.name}.csv"
            if self.make_csv_at_prepare:
                attachments = self.env["ir.attachment"].search(
                    [("name", "=", filename)], limit=1
                )
                if len(attachments) == 0:
                    _logger.error("Cannot find attachment with name %s", filename)
                    continue
                csv_data = base64.b64decode(attachments[0].datas)
            else:
                data = self.prepare_csv_for_batch(batch)
                csv_data = data.getvalue()
            files = {"data": (filename, csv_data)}

            bulk_trans_url = payment_endpoint_url
            headers = {
                "Platform-TenantId": tenant_id,
                "Type": self.batch_type_header,
                "Purpose": self.batch_purpose_header,
                "filename": filename,
                "X-CorrelationID": x_correlation_id,
            }

            try:
                res = requests.post(
                    bulk_trans_url,
                    headers=headers,
                    files=files,
                    timeout=batch_request_timeout,
                    verify=False,
                )
                res.raise_for_status()
                jsonResponse = res.json()
                _logger.info(f"PHEE API: jsonResponse: {jsonResponse}")
                for key, value in jsonResponse.items():
                    _logger.info(f"PHEE API: key:value = {key}:{value}")

            except HTTPError as http_err:
                _logger.error(f"PHEE API: HTTP error occurred: {http_err}")
                continue
            except Exception as err:
                _logger.error(f"PHEE API: Other error occurred: {err}")
                continue

            batch.batch_has_started = True
            batch.payment_ids.write({"state": "sent"})

            # _logger.info("PHEE API: data: %s" % csv_data)
            _logger.info(f"PHEE API: res: {res} - {res.content}")

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
                payee_id_type_to_send = self.id_for_payee_id.name

            for reg_id in payment.partner_id.reg_ids:
                if reg_id.id_type.id == self.id_for_payee_id.id:
                    return payee_id_type_to_send, reg_id.value
        # TODO: Deal with no bank acc and/or ID type not matching any available IDs
        return None, None

    def prepare_csv_for_batch(self, batch, delimiter=",", quoting=csv.QUOTE_MINIMAL):
        payment_mode = self.payment_mode
        payer_identifier_type = self.payer_id_type
        payer_identifier = self.payer_id

        disbursement_note = (
            f"Program: {batch.program_id.name}. Cycle ID - {batch.cycle_id.name}"
        )

        data = StringIO()
        csv_writer = csv.writer(data, delimiter=delimiter, quoting=quoting)
        header = [
            "id",
            "request_id",
            "payment_mode",
            "payer_identifier_type",
            "payer_identifier",
            "payee_identifier_type",
            "payee_identifier",
            "amount",
            "currency",
            "note",
        ]
        csv_writer.writerow(header)
        for row, payment_id in enumerate(batch.payment_ids):
            payee_identifier_type, payee_identifier = self._get_dfsp_id_and_type(
                payment_id
            )
            row = [
                row,
                payment_id.name,
                payment_mode,
                payer_identifier_type,
                payer_identifier,
                payee_identifier_type,
                payee_identifier,
                payment_id.amount_issued,
                payment_id.currency_id.name,
                disbursement_note,
            ]
            csv_writer.writerow(row)

        return data

    def create_update_csv_attachment(self, filename, csv_data_bin):
        attach_search_result = self.env["ir.attachment"].search(
            [("name", "=", filename)]
        )
        csv_data_base64 = base64.b64encode(csv_data_bin)
        if len(attach_search_result) > 0:
            attach_search_result.write(
                {
                    "datas": csv_data_base64,
                    "public": False,
                    "type": "binary",
                }
            )
        else:
            self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "datas": csv_data_base64,
                    "public": False,
                    "type": "binary",
                }
            )
