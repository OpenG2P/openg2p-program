# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class G2PEntitlementWizard(models.TransientModel):
    _name = "g2p.entitlement.wizard"
    _description = "G2P Entitlement Wizard"

    _inherit = "g2p.entitlement"

    def create_entitlement(self):
        return self.env["g2p.entitlement"].create(
            {
                "program_id": self.program_id.id,
                "partner_id": self.partner_id.id,
                "is_cash_entitlement": True,
                "cycle_id": self.program_id.default_active_cycle.id,
                "initial_amount": self.initial_amount,
                "valid_from": self.valid_from,
                "valid_until": self.valid_until,
            }
        )
