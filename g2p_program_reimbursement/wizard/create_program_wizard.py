from odoo import fields, models


class G2PCreateNewReimbursementProgramWiz(models.TransientModel):
    _inherit = "g2p.program.create.wizard"

    is_reimbursement_program = fields.Boolean(default=False)

    def create_program(self):
        if self.is_reimbursement_program:
            self.env.context = {"is_reimbursement_program": True}

        res = super().create_program()
        for rec in self:
            program = self.env["g2p.program"].browse(res["res_id"])
            program.is_reimbursement_program = rec.is_reimbursement_program
            return res
