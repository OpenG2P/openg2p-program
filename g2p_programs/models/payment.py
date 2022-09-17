# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging
from uuid import uuid4

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class G2PPayment(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = "g2p.payment"
    _description = "Payment"
    _order = "id desc"

    name = fields.Many2one("g2p.entitlement", "Entitlement", required=True)
    cycle_id = fields.Many2one("g2p.cycle", "Cycle", readonly=True)
    partner_id = fields.Many2one(
        "res.partner", related="name.partner_id", string="Beneficiary", readonly=True
    )

    # batch_id = fields.Many2one("g2p.payment.batch", "Payment Batch")

    state = fields.Selection(
        selection=[
            ("issued", "Issued"),
            ("sent", "Sent"),
            ("paid", "Paid"),
            ("failed", "Failed"),
        ],
        string="Status",
        required=True,
        default="issued",
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

    @api.depends("name.cycle_id.program_id.journal_id")
    def _compute_journal_id(self):
        for record in self:
            record.journal_id = (
                record.name
                and record.name.cycle_id
                and record.name.cycle_id.program_id
                and record.name.cycle_id.program_id.journal_id
                and record.name.cycle_id.program_id.journal_id.id
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
    external_batch_ref = fields.Char("External Batch Reference #")

    batch_has_completed = fields.Boolean()

    payment_ids = fields.Many2many("g2p.payment", "Payments")

    # This set of fields hold the current statistics of the payment batch
    # We store this so that we can display this information without calling the payment system
    stats_issued_transactions = fields.Integer("Issued Transaction Statistics")
    stats_issued_amount = fields.Float("Issued Amount Statistics")
    stats_sent_transactions = fields.Integer("Sent Transactions Statistics")
    stats_sent_amount = fields.Float("Sent Amount Statistics")
    stats_paid_transactions = fields.Integer("Paid Transactions Statistics")
    stats_paid_amount = fields.Float("Paid Amount Statistics")
    stats_failed_transactions = fields.Integer("Failed Transactions Statistics")
    stats_failed_amount = fields.Float("Failed Amount Statistics")

    stats_datetime = fields.Datetime("Statistics Date/Time")
