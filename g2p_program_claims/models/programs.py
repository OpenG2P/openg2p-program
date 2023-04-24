from odoo import fields, models


class G2PPrograms(models.Model):
    _inherit = "g2p.program"

    is_claims_program = fields.Boolean(default=False)

    claim_original_program_ids = fields.One2many("g2p.program", "claim_program_id")

    claim_program_id = fields.Many2one("g2p.program")
