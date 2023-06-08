import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DefaultEligibilityManager(models.Model):
    _inherit = "g2p.program_membership.manager.default"

    def enroll_eligible_registrants(self, program_memberships):
        res = super(DefaultEligibilityManager, self).enroll_eligible_registrants(
            program_memberships
        )
        for rec in program_memberships:
            if (
                rec.latest_registrant_info
                and rec.latest_registrant_info.status == "active"
            ):
                rec.latest_registrant_info.status = "inprogress"
        return res
