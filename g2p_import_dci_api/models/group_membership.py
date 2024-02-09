from odoo import api, fields, models


class OpenG2PGroupMembership(models.Model):
    _inherit = "g2p.group.membership"

    is_created_from_social_registry = fields.Boolean(
        "Created from Social Registry",
        compute="_compute_is_created_from_social_registry",
        store=True,
    )

    @api.depends("group")
    def _compute_is_created_from_social_registry(self):
        for rec in self:
            rec.is_created_from_social_registry = (
                rec.group.grp_is_created_from_social_registry
            )
