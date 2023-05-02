# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class G2PCreateEntitlementWizard(models.TransientModel):
    _name = "g2p.entitlement.wizard"
    _description = "Create a New Entitlement Wizard"

    partner_id = fields.Many2one(
        "res.partner",
        "Registrant",
        help="A beneficiary",
        required=True,
        domain=[("is_registrant", "=", True)],
    )

    # initial_amount = fields.Monetary(required=True, currency_field="currency_id")
