import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DefaultEligibilityManager(models.Model):
    _inherit = "g2p.program_membership.manager.default"

    def enroll_eligible_registrants(self, program_memberships):
        res = super().enroll_eligible_registrants(program_memberships)
        for rec in program_memberships:
            self.env["g2p.program.registrant_info"].trigger_latest_status_membership(
                rec, "inprogress", check_states=("active",)
            )
        return res
