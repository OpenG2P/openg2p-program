# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from werkzeug.exceptions import Forbidden

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class DefaultEntitlementManagerApproval(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    mapping_ids = fields.One2many(
        "g2p.program.approval.mapping", "default_entitlement_approval_manager_id"
    )

    def approve_entitlements(self, entitlements):
        user_err = 0
        undefined_err = 0

        entitlements_approvable = entitlements.filtered(
            lambda x: x.state in ("draft", "pending_validation")
        )
        entitlements_remain = entitlements - entitlements_approvable

        # TODO: Processing this one by one for now. Change this to process by group later
        entitlements_to_approve = None
        for entitlement in entitlements_approvable:
            if entitlement.state == "draft":
                entitlement.state = "pending_validation"
            try:
                success, next_mapping = self.mapping_ids.get_next_mapping(
                    entitlement.approval_state
                )
                if success:
                    if not next_mapping:
                        entitlements_to_approve = (
                            (entitlements_to_approve + entitlement)
                            if entitlements_to_approve
                            else entitlement
                        )
                        continue
                    else:
                        entitlement.approval_state = next_mapping.state
                else:
                    undefined_err += 1
            except Forbidden:
                user_err += 1

        final_err = user_err + undefined_err
        final_message = ""
        entitlements_to_approve = (
            (entitlements_to_approve + entitlements_remain)
            if entitlements_to_approve
            else entitlements_remain
        )
        if entitlements_to_approve:
            res_state_err, res_message = super(
                DefaultEntitlementManagerApproval, self
            ).approve_entitlements(entitlements_to_approve)
            if not res_state_err:
                final_err = 0
            if res_message:
                final_message += res_message

        if user_err:
            final_message += _(f"Not allowed to approve {user_err} entitlements.")
        if undefined_err:
            final_message += _(f"Unknown error for {undefined_err} entitlements.")

        return final_err, final_message

    def show_approve_entitlements(self, entitlement):
        # TODO: Processing this one by one for now. Change this to process by group later
        entitlement.ensure_one()
        show_ent = entitlement.state in ("draft", "pending_validation")
        try:
            self.mapping_ids.get_next_mapping(entitlement.approval_state)
        except Forbidden:
            show_ent = False
        return show_ent
