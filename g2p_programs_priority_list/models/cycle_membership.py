from odoo import fields, models


class G2PCycleMembershipInherited(models.Model):
    _inherit = "g2p.cycle.membership"

    rank = fields.Integer(index=True)
