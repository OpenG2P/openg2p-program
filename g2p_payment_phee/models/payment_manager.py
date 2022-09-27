# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models


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

        ctr = 0
        vals = []
        payments_to_add_ids = []
        for entitlement_id in entitlements_with_payments_to_create:
            payment = self.env["g2p.payment"].create(
                {
                    "entitlement_id": entitlement_id.id,
                    "cycle_id": entitlement_id.cycle_id.id,
                    "amount_issued": entitlement_id.initial_amount,
                    "payment_fee": entitlement_id.transfer_fee,
                    "state": "issued",
                    # "account_number": self._get_account_number(entitlement_id),
                }
            )
            vals.append((4, payment.id))
            payments_to_add_ids.append(payment.id)
            ctr += 1
        if ctr > 0:
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
