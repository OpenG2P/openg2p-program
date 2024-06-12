# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from werkzeug.exceptions import Forbidden

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class DefaultEntitlementManagerApproval(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    approval_mapping_ids = fields.Many2many(
        "g2p.program.approval.mapping",
        compute="_compute_approval_mapping_ids",
        inverse="_inverse_approval_mapping_ids",
        ondelete="cascade",
    )

    def _compute_approval_mapping_ids(self):
        for rec in self:
            approval_mappings = self.env["g2p.program.approval.mapping"].search(
                [("entitlement_manager_ref", "=", f"{rec._name}, {rec.id}")]
            )
            rec.approval_mapping_ids = [(4, mapping.id) for mapping in approval_mappings]

    def _inverse_approval_mapping_ids(self):
        for rec in self:
            old_approval_mapping_ids = self.env["g2p.program.approval.mapping"].search(
                [("entitlement_manager_ref", "=", f"{rec._name}, {rec.id}")]
            )

            to_delete = old_approval_mapping_ids - rec.approval_mapping_ids
            if to_delete:
                to_delete.unlink()

            to_add = rec.approval_mapping_ids - old_approval_mapping_ids
            if to_add:
                to_add.entitlement_manager_ref = f"{rec._name}, {rec.id}"

    def approve_entitlements(self, entitlements):
        user_err = 0
        undefined_err = 0

        entitlements_approvable = entitlements.filtered(lambda x: x.state in ("draft", "pending_validation"))
        entitlements_remain = entitlements - entitlements_approvable

        # TODO: Processing this one by one for now. Change this to process by group later
        entitlements_to_approve = None
        for entitlement in entitlements_approvable:
            if entitlement.state == "draft":
                entitlement.state = "pending_validation"
            try:
                success, next_mapping = self.approval_mapping_ids.get_next_mapping(entitlement.approval_state)
                _logger.debug(
                    "Program Approval: approve entitlement. Next Mapping success - %s, next-mapping - %s",
                    success,
                    next_mapping,
                )
                if success:
                    if not next_mapping:
                        entitlements_to_approve = (
                            (entitlements_to_approve + entitlement)
                            if entitlements_to_approve
                            else entitlement
                        )
                        _logger.debug(
                            "Program Approval: approve entitlement. No next mapping to be approved - %s",
                            entitlements_to_approve,
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
            res_state_err, res_message = super(DefaultEntitlementManagerApproval, self).approve_entitlements(
                entitlements_to_approve
            )
            if not final_err:
                final_err = res_state_err
            if res_message:
                final_message += res_message

        if user_err:
            final_message += _(f"Not allowed to approve {user_err} entitlements.")
        if undefined_err:
            final_message += _(f"Unknown error for {undefined_err} entitlements.")

        _logger.debug(
            "Program Approval: approve entitlement. Final Res: err_code - %s, message - %s",
            final_err,
            final_message,
        )
        return final_err, final_message

    def show_approve_entitlements(self, entitlement):
        # TODO: Processing this one by one for now. Change this to process by group later
        entitlement.ensure_one()
        show_ent = entitlement.state in ("draft", "pending_validation")
        try:
            self.approval_mapping_ids.get_next_mapping(entitlement.approval_state)
        except Forbidden:
            show_ent = False
        return show_ent
