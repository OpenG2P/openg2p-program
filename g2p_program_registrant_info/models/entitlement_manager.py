import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DefaultEntitlementManagerRegInfo(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def approve_entitlements(self, entitlements):
        state_err, message = super(
            DefaultEntitlementManagerRegInfo, self
        ).approve_entitlements(entitlements)
        for rec in entitlements:
            prog_mem = rec.partner_id.program_membership_ids.filtered(
                lambda x: x.program_id.id == rec.program_id.id
            )
            if prog_mem.latest_registrant_info_status != "closed":
                prog_mem.latest_registrant_info.status = "closed"
        return state_err, message
