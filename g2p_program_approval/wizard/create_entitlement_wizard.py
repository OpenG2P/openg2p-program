# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PCreateEntitlementWizard(models.TransientModel):
    _name = "g2p.entitlement.wizard"
    _description = "Create a New Entitlement Wizard"

    partner_id = fields.Many2one(
        "res.partner",
        "Beneficiary",
        help="A beneficiary",
        required=True,
        domain=[("is_registrant", "=", True)],
    )

    program_id = fields.Many2one("g2p.program")

    initial_amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency")

    valid_from = fields.Date(required=False)
    valid_until = fields.Date(
        default=lambda self: fields.Date.add(fields.Date.today(), years=1)
    )

    def create_entitlement(self):

        record = self.env["g2p.entitlement"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("program_id", "=", self.program_id.id),
            ]
        )

        if record.id:
            # TODO check status and then update the record
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
            # TODO create the record
            pass
