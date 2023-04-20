from odoo import fields, models


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    program_registrant_info_ids = fields.One2many(
        "g2p.program.registrant_info", "program_membership_id"
    )
