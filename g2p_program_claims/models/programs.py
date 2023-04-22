from odoo import fields, models


class G2PPrograms(models.Model):
    _inherit = "g2p.program"

    is_claims_program = fields.Boolean(default=False)
