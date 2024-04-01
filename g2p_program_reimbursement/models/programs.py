from odoo import _, fields, models


class G2PPrograms(models.Model):
    _inherit = "g2p.program"

    is_reimbursement_program = fields.Boolean(default=False)

    reimbursement_program_id = fields.Many2one("g2p.program")

    def open_eligible_beneficiaries_form(self):
        res = super().open_eligible_beneficiaries_form()
        if self.is_reimbursement_program:
            res["name"] = _("Service Providers")
        return res

    def open_cycles_form(self):
        res = super().open_cycles_form()
        if self.is_reimbursement_program:
            res["views"] = [
                # To update the following tree view when there are modifications
                [self.env.ref("g2p_programs.view_cycle_tree").id, "tree"],
                [
                    self.env.ref("g2p_program_reimbursement.view_cycle_reimbursement_form").id,
                    "form",
                ],
            ]
        return res
