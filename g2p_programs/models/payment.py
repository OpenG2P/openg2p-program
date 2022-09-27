# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging
from http.client import HTTPConnection
from uuid import uuid4

import requests
from requests.exceptions import HTTPError

from odoo import api, fields, models

log = logging.getLogger("urllib3")
log.setLevel(logging.DEBUG)

# logging from urllib3 to console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

# print statements from `http.client.HTTPConnection` to console/stdout
HTTPConnection.debuglevel = 1

_logger = logging.getLogger(__name__)


class G2PPayment(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = "g2p.payment"
    _description = "Payment"
    _order = "id desc"

    name = fields.Char(
        "Internal Reference #", default=str(uuid4()), readonly=True, copy=False
    )
    entitlement_id = fields.Many2one("g2p.entitlement", "Entitlement", required=True)
    cycle_id = fields.Many2one("g2p.cycle", "Cycle", readonly=True)
    program_id = fields.Many2one(
        "g2p.program", related="cycle_id.program_id", readonly=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="entitlement_id.partner_id",
        string="Beneficiary",
        readonly=True,
    )

    batch_id = fields.Many2one("g2p.payment.batch", "Payment Batch")

    state = fields.Selection(
        selection=[
            ("issued", "Issued"),
            ("sent", "Sent"),
            ("reconciled", "Reconciled"),
        ],
        string="Status",
        required=True,
        default="issued",
    )
    status = fields.Selection(
        selection=[
            ("paid", "Paid"),
            ("failed", "Failed"),
        ],
        string="Payment Status",
    )
    status_is_final = fields.Boolean("Is final payment status", default=False)
    status_datetime = fields.Datetime()

    # We should have a snapshot of the account number from the beneficiary at the point of creating the payment
    account_number = fields.Char()

    amount_issued = fields.Monetary(required=True, currency_field="currency_id")
    amount_paid = fields.Monetary(currency_field="currency_id")
    issuance_date = fields.Datetime(
        default=fields.Datetime.now
    )  # Should default to Datetime.Now()
    payment_datetime = fields.Datetime()

    payment_fee = fields.Monetary(currency_field="currency_id")

    currency_id = fields.Many2one(
        "res.currency", readonly=True, related="journal_id.currency_id"
    )

    journal_id = fields.Many2one(
        "account.journal",
        "Program Journal",
        store=True,
        compute="_compute_journal_id",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.depends("entitlement_id.cycle_id.program_id.journal_id")
    def _compute_journal_id(self):
        for record in self:
            record.journal_id = (
                record.entitlement_id
                and record.entitlement_id.cycle_id
                and record.entitlement_id.cycle_id.program_id
                and record.entitlement_id.cycle_id.program_id.journal_id
                and record.entitlement_id.cycle_id.program_id.journal_id.id
                or None
            )

    def check_account_status(self):
        # Checks if the account is available for payment
        # Simple implementation will check if a account number has been set
        pass

    def issue_payment(self):
        pass


class G2PPaymentBatch(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = "g2p.payment.batch"
    _description = "Payment Batch"
    _order = "id desc"

    name = fields.Char(
        "Internal Batch Reference #", default=str(uuid4()), readonly=True, copy=False
    )
    cycle_id = fields.Many2one("g2p.cycle", "Cycle", readonly=True)
    program_id = fields.Many2one(
        "g2p.program", related="cycle_id.program_id", string="Program", readonly=True
    )
    external_batch_ref = fields.Char("External Batch Reference #")

    batch_has_completed = fields.Boolean()

    payment_ids = fields.Many2many("g2p.payment", string="Payments")

    # This set of fields hold the current statistics of the payment batch
    # We store this so that we can display this information without calling the payment system
    stats_issued_transactions = fields.Integer(
        "Issued Transaction Statistics", readonly=True
    )
    stats_issued_amount = fields.Float("Issued Amount Statistics", readonly=True)
    stats_sent_transactions = fields.Integer(
        "Sent Transactions Statistics", readonly=True
    )
    stats_sent_amount = fields.Float("Sent Amount Statistics", readonly=True)
    stats_paid_transactions = fields.Integer(
        "Paid Transactions Statistics", readonly=True
    )
    stats_paid_amount = fields.Float("Paid Amount Statistics", readonly=True)
    stats_failed_transactions = fields.Integer(
        "Failed Transactions Statistics", readonly=True
    )
    stats_failed_amount = fields.Float("Failed Amount Statistics", readonly=True)

    stats_datetime = fields.Datetime("Statistics Date/Time")

    def send_payments(self):
        # Bulk Transfer to PHEE API
        # data = io.StringIO("")
        for rec in self:
            payment_endpoint_url = rec.program_id.get_manager(
                rec.program_id.MANAGER_PAYMENT
            ).payment_endpoint_url
            tenant_id = rec.program_id.get_manager(
                rec.program_id.MANAGER_PAYMENT
            ).tenant_id

            bulk_trans_url = f"{payment_endpoint_url}/{rec.name}/test-payload.csv"
            headers = {
                "Platform-TenantId": tenant_id,
            }
            data = "id,request_id,payment_mode,account_number,amount,currency,note\n"
            for row in rec.payment_ids:
                # TODO: Get data for payment_mode and account_number
                payment_mode = "slcb"
                account_number = "SE0000000000001234567890"
                data += f"{row.id},{rec.name},{payment_mode},{account_number},"
                data += f"{row.amount_issued},{row.currency_id.name},{row.partner_id.name}\n"

            try:
                res = requests.post(
                    bulk_trans_url, headers=headers, data=data, verify=False
                )
                res.raise_for_status()
                # access JSOn content
                jsonResponse = res.json()
                _logger.info(f"PHEE API: jsonResponse: {jsonResponse}")
                for key, value in jsonResponse.items():
                    _logger.info(f"PHEE API: key:value = {key}:{value}")

            except HTTPError as http_err:
                _logger.info(f"PHEE API: HTTP error occurred: {http_err}")
            except Exception as err:
                _logger.info(f"PHEE API: Other error occurred: {err}")

            _logger.info("PHEE API: data: %s" % data)
            _logger.info("PHEE API: res: %s - %s" % (res, res.content))
