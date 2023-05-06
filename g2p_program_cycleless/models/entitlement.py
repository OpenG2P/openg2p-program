# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    def create_entitlement(self):

        record = self.env["g2p.entitlement"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("program_id", "=", self.program_id.id),
            ]
        )

        if record.id:
            if record.state == "draft":
                record.update(
                    {
                        "initial_amount": self.initial_amount,
                        "valid_from": self.valid_from,
                        "valid_until": self.valid_until,
                    }
                )
            else:
                _logger.error("Not allowed to update the Entitlement")
        else:

            record.create(
                {
                    "partner_id": self.partner_id.id,
                    "program_id": self.program_id.id,
                    "initial_amount": self.initial_amount,
                    "valid_from": self.valid_from,
                    "valid_until": self.valid_until,
                    "is_cash_entitlement": True,
                    "cycle_id": self.program_id.default_active_cycle.id,
                }
            )
