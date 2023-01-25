# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import base64
import csv
import logging
from io import StringIO
from uuid import uuid4

from odoo import Command, _, api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _name = "g2p.program.payment.manager"
    _description = "Payment Manager"
    _inherit = "g2p.manager.mixin"

    program_id = fields.Many2one("g2p.program", "Program")

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = ("g2p.program.payment.manager.default", "Default")
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class BasePaymentManager(models.AbstractModel):
    _name = "g2p.base.program.payment.manager"
    _inherit = "base.programs.manager"
    _description = "Base Payment Manager"

    name = fields.Char("Manager Name", required=True)
    program_id = fields.Many2one("g2p.program", string="Program", required=True)

    def prepare_payments(self, entitlements):
        """
        This method is used to prepare the payment list of the entitlements.
        :param entitlements: The entitlements.
        :return:
        """
        raise NotImplementedError()

    def send_payments(self, batches):
        """
        This method is used to send the payment list by batch.
        :param batches: The payment batches.
        :return:
        """
        raise NotImplementedError()

    def validate_accounts(self, entitlements):
        """
        This method is used to that accounts exist to pay the entitlements
        :param entitlements: The list of entitlements
        :return:
        """
        raise NotImplementedError()


class DefaultFilePaymentManager(models.Model):
    _name = "g2p.program.payment.manager.default"
    _inherit = ["g2p.base.program.payment.manager", "g2p.manager.source.mixin"]
    _description = "Default Payment Manager"

    create_batch = fields.Boolean("Automatically Create Batch")
    currency_id = fields.Many2one(
        "res.currency", related="program_id.journal_id.currency_id", readonly=True
    )

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
            # _logger.debug("DEBUG! payments_to_create: %s", payments_to_create)

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
                message = _("%s new payments was issued.", len(payments_to_add_ids))
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
                "title": _("Payment"),
                "message": message + refresh,
                "links": links,
                "sticky": True,
                "type": kind,
            },
        }

    def send_payments(self, batches):
        # Create a payment list (CSV)
        # _logger.debug("DEBUG! send_payments Manager: DEFAULT")
        for rec in batches:
            filename = f"{rec.name}.csv"
            data = StringIO()
            csv_writer = csv.writer(data, quoting=csv.QUOTE_MINIMAL)
            header = [
                "row_number",
                "internal_payment_reference",
                "account_number",
                "beneficiary_name",
                "amount",
                "currency",
                "details_of_payment",
            ]
            csv_writer.writerow(header)
            for row, payment_id in enumerate(rec.payment_ids):
                account_number = ""
                if payment_id.partner_id.bank_ids:
                    account_number = payment_id.partner_id.bank_ids[0].iban
                details_of_payment = (
                    f"{payment_id.program_id.name} - {payment_id.cycle_id.name}"
                )
                row = [
                    row,
                    payment_id.name,
                    account_number,
                    payment_id.partner_id.name,
                    payment_id.amount_issued,
                    payment_id.currency_id.name,
                    details_of_payment,
                ]
                csv_writer.writerow(row)
            csv_data = base64.encodebytes(bytearray(data.getvalue(), "utf-8"))
            # Attach the generated CSV to payment batch
            self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "res_model": "g2p.payment.batch",
                    "res_id": rec.id,
                    "type": "binary",
                    "store_fname": filename,
                    "mimetype": "text/csv",
                    "datas": csv_data,
                }
            )

            # _logger.debug("DEFAULT Payment Manager: data: %s" % csv_data)

    def _get_account_number(self, entitlement):
        return entitlement.partner_id.get_payment_token(entitlement.program_id)
