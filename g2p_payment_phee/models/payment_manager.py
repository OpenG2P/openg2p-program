# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import csv
import logging
from http.client import HTTPConnection
from io import StringIO
from uuid import uuid4

import requests
from requests.exceptions import HTTPError

from odoo import Command, _, api, fields, models

log = logging.getLogger("urllib3")
log.setLevel(logging.DEBUG)

# logging from urllib3 to console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

# print statements from `http.client.HTTPConnection` to console/stdout
HTTPConnection.debuglevel = 1

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
    auth_token = fields.Char("Authentication Token")  # A JWT

    # Payment parameters
    file_name = fields.Char("Filename")  # "openspp-payload.csv"

    # Payment reference
    # phee_batch_id = None
    # payment_details_url = None

    # TODO: optimize code to do in a single query.
    def prepare_payments(self, cycle):
        entitlements = cycle.entitlement_ids.filtered(lambda a: a.state == "approved")
        if entitlements:
            entitlements_ids = entitlements.ids

            # Filter out entitlements without payments
            entitlements_with_payments = (
                self.env["g2p.payment"]
                .search([("entitlement_id", "in", entitlements_ids)])
                .mapped("entitlement_id.id")
            )

            # Todo: fix issue with variable payments_to_create is generating list of list
            if entitlements_with_payments:
                payments_to_create = [
                    entitlements_ids
                    for entitlement_id in entitlements_ids
                    if entitlement_id not in entitlements_with_payments
                ]
            else:
                payments_to_create = entitlements_ids

            entitlements_with_payments_to_create = self.env["g2p.entitlement"].browse(
                payments_to_create
            )
            # _logger.info("DEBUG! payments_to_create: %s", payments_to_create)

            vals = []
            payments_to_add_ids = []
            for entitlement_id in entitlements_with_payments_to_create:
                payment = self.env["g2p.payment"].create(
                    {
                        "name": str(uuid4()),
                        "entitlement_id": entitlement_id.id,
                        "cycle_id": entitlement_id.cycle_id.id,
                        "amount_issued": entitlement_id.initial_amount,
                        "payment_fee": entitlement_id.transfer_fee,
                        "state": "issued",
                        # "account_number": self._get_account_number(entitlement_id),
                    }
                )
                # Link the issued payment record to the many2many field payment_ids.
                # vals.append((Command.LINK, payment.id))
                vals.append(Command.link(payment.id))
                payments_to_add_ids.append(payment.id)
            if payments_to_add_ids:
                # Create payment batch
                if self.create_batch:
                    new_batch_vals = {
                        "cycle_id": cycle.id,
                        "payment_ids": vals,
                        "stats_datetime": fields.Datetime.now(),
                    }
                    batch = self.env["g2p.payment.batch"].create(new_batch_vals)
                    # Update processed payments batch_id
                    self.env["g2p.payment"].browse(payments_to_add_ids).update(
                        {"batch_id": batch.id}
                    )

                kind = "success"
                message = _("%s new payments was issued.") % len(payments_to_add_ids)
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
        for rec in batches:
            # TODO: determine the appropriate filename
            filename = "test-payload.csv"
            bulk_trans_url = f"{payment_endpoint_url}/{rec.name}/{filename}"
            headers = {
                "Platform-TenantId": tenant_id,
            }
            data = StringIO()
            csv_writer = csv.writer(data, quoting=csv.QUOTE_MINIMAL)
            header = [
                "id",
                "request_id",
                "payment_mode",
                "account_number",
                "amount",
                "currency",
                "note",
            ]
            csv_writer.writerow(header)
            for row, payment_id in enumerate(rec.payment_ids):
                # TODO: Get data for payment_mode and account_number
                payment_mode = "slcb"
                account_number = "SE0000000000001234567890"
                row = [
                    row,
                    rec.name,
                    payment_mode,
                    account_number,
                    payment_id.amount_issued,
                    payment_id.currency_id.name,
                    payment_id.partner_id.name,
                ]
                csv_writer.writerow(row)

            csv_data = data.getvalue()

            try:
                res = requests.post(
                    bulk_trans_url, headers=headers, data=csv_data, verify=False
                )
                res.raise_for_status()
                # TODO: Perform detailed parsing of jsonResponse
                # access JSOn content
                jsonResponse = res.json()
                _logger.info(f"PHEE API: jsonResponse: {jsonResponse}")
                for key, value in jsonResponse.items():
                    _logger.info(f"PHEE API: key:value = {key}:{value}")

            except HTTPError as http_err:
                _logger.info(f"PHEE API: HTTP error occurred: {http_err}")
            except Exception as err:
                _logger.info(f"PHEE API: Other error occurred: {err}")

            # _logger.info("PHEE API: data: %s" % csv_data)
            _logger.info("PHEE API: res: %s - %s" % (res, res.content))

    def _get_account_number(self, entitlement):
        return entitlement.partner_id.get_payment_token(entitlement.program_id)
