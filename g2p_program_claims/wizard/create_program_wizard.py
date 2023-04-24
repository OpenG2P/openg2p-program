from odoo import fields, models


class G2PCreateNewClaimsProgramWiz(models.TransientModel):
    _inherit = "g2p.program.create.wizard"

    is_claims_program = fields.Boolean(default=False)

    def create_program(self):
        res = super(G2PCreateNewClaimsProgramWiz, self).create_program()
        for rec in self:
            program = self.env["g2p.program"].browse(res["res_id"])
            program.is_claims_program = rec.is_claims_program
            return res
