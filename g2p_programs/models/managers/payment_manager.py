# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models

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

    currency_id = fields.Many2one(
        "res.currency", related="program_id.journal_id.currency_id", readonly=True
    )

    def prepare_payments(self, cycle):
        entitlements_ids = cycle.entitlement_ids.ids

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

        # Todo: Create payment batch
        # batch = self.env["g2p.paymentbatch"].create()

        ctr = 0
        for entitlement_id in entitlements_with_payments_to_create:
            self.env["g2p.payment"].create(
                {
                    "entitlement_id": entitlement_id.id,
                    "cycle_id": entitlement_id.cycle_id.id,
                    "amount_issued": entitlement_id.initial_amount,
                    "payment_fee": entitlement_id.transfer_fee,
                    "state": "issued",
                    # "account_number": self._get_account_number(entitlement_id),
                    # "batch_id": batch.id,
                }
            )
            ctr += 1
        if ctr > 0:
            kind = "success"
            message = _("%s new payments was issued.") % ctr
            links = [
                {
                    "label": "Refresh Page",
                }
            ]
        else:
            kind = "danger"
            message = _("There are no new payments issued!")
            links = [{}]

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Payment"),
                "message": message + " %s",
                "links": links,
                "sticky": True,
                "type": kind,
            },
        }

    def _get_account_number(self, entitlement):
        return entitlement.partner_id.get_payment_token(entitlement.program_id)

    def validate_entitlements(self, cycle, cycle_memberships):
        # TODO: Change the status of the entitlements to `validated` for this members.
        # move the funds from the program's wallet to the wallet of each Beneficiary that are validated
        pass
