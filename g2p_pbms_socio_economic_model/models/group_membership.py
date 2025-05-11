# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PGroupMembershipInherit(models.Model):
    _inherit = "g2p.group.membership"

    employment_status = fields.Selection(related="individual.employment_status")

    def get_household_head(self, registrant):
        if registrant.is_group:
            for member in registrant.group_membership_ids:
                if member.kind and "Head" in [kind.name for kind in member.kind]:
                    return member.individual

        else:
            for member in registrant.individual_membership_ids:
                if member.kind and "Head" in [kind.name for kind in member.kind]:
                    return member.individual
