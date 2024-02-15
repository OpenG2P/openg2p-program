from odoo import fields, models


class G2PCycle(models.Model):
    _inherit = "g2p.cycle"

    is_reimbursement_program = fields.Boolean(
        related="program_id.is_reimbursement_program"
    )

    def open_cycle_form(self):
        res = super().open_cycle_form()
        if self.is_reimbursement_program:
            res["view_id"] = self.env.ref(
                "g2p_program_reimbursement.view_cycle_reimbursement_form"
            ).id
        return res
