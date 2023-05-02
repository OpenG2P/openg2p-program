from odoo import fields, models


class G2PCycle(models.Model):
    _inherit = "g2p.cycle"

    is_claims_program = fields.Boolean(related="program_id.is_claims_program")

    def open_cycle_form(self):
        res = super(G2PCycle, self).open_cycle_form()
        if self.is_claims_program:
            res["view_id"] = self.env.ref(
                "g2p_program_claims.view_cycle_claims_form"
            ).id
        return res
