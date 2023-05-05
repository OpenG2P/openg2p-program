from odoo import fields, models


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    payment_status = fields.Selection(
        [("paid", "Paid"), ("notpaid", "Not Paid")], compute="_compute_payment_status"
    )
    payment_date = fields.Date(compute="_compute_payment_date")

    def _compute_payment_status(self):
        for rec in self:
            for payment in rec.payment_ids:
                if payment.status == "paid":
                    rec.payment_status = "paid"
                    break
            if rec.payment_status != "paid":
                rec.payment_status = "notpaid"

    def _compute_payment_date(self):
        for rec in self:
            for payment in rec.payment_ids:
                rec.payment_date = payment.payment_datetime
