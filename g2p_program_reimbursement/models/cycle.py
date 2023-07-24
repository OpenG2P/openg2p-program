from odoo import fields, models


class G2PCycle(models.Model):
    _inherit = "g2p.cycle"

    is_reimbursement_program = fields.Boolean(
        related="program_id.is_reimbursement_program"
    )

    edit_css = fields.Html(
        sanitize=False,
        compute="_compute_css",
    )

    def open_cycle_form(self):
        res = super(G2PCycle, self).open_cycle_form()
        if self.is_reimbursement_program:
            res["view_id"] = self.env.ref(
                "g2p_program_reimbursement.view_cycle_reimbursement_form"
            ).id
        return res

    def _compute_css(self):
        for rec in self:
            # To Remove Edit Option
            if rec.state not in "draft":
                rec.edit_css = (
                    "<style>.o_form_button_edit {display: none !important;}</style>"
                )
            else:
                rec.edit_css = False
