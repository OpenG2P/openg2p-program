import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DefaultEntitlementManagerRegInfo(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def prepare_entitlements(self, cycle, beneficiaries):
        ents = super(DefaultEntitlementManagerRegInfo, self).prepare_entitlements(
            cycle, beneficiaries
        )
        if ents:
            for ent in ents:
                self.env[
                    "g2p.program.registrant_info"
                ].assign_reg_info_to_entitlement_from_membership(ent)
        return ents

    def approve_entitlements(self, entitlements):
        state_err, message = super(
            DefaultEntitlementManagerRegInfo, self
        ).approve_entitlements(entitlements)
        if not state_err:
            for rec in entitlements:
                self.env[
                    "g2p.program.registrant_info"
                ].trigger_latest_status_of_entitlement(
                    rec, "completed", check_states=()
                )
        return state_err, message
