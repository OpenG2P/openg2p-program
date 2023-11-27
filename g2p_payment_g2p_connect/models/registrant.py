# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    mode_of_payment = fields.Selection(
        [
            ("cash", "Cash"),
            ("voucher", "Voucher"),
            ("digital", "Digital"),
        ]
    )

    def get_registrants_or_group_heads(self):
        res = None
        head_membership = self.env.ref(
            "g2p_registry_membership.group_membership_kind_head"
        )
        for partner in self:
            if partner.is_group:
                partner = partner.group_membership_ids.filtered(
                    lambda x: head_membership.id in x.kind
                )
                partner = partner[0].individual if partner else None
            if not res:
                res = partner
            else:
                res += partner
        return res
