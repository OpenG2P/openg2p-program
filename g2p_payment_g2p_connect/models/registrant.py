# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    # TODO: Move this field to the correct place later
    mode_of_payment = fields.Selection(
        [
            ("cash", "Cash"),
            ("voucher", "Voucher"),
            ("digital", "Digital"),
        ]
    )
