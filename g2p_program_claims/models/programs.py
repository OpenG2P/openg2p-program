from odoo import _, fields, models


class G2PPrograms(models.Model):
    _inherit = "g2p.program"

    is_claims_program = fields.Boolean(default=False)

    claim_original_program_ids = fields.One2many("g2p.program", "claim_program_id")

    claim_program_id = fields.Many2one("g2p.program")

    supporting_documents_store = fields.Many2one("storage.backend")

    def open_eligible_beneficiaries_form(self):
        res = super(G2PPrograms, self).open_eligible_beneficiaries_form()
        if self.is_claims_program:
            res["name"] = _("Vendors")
        return res

    def open_cycles_form(self):
        res = super(G2PPrograms, self).open_cycles_form()
        if self.is_claims_program:
            res["views"] = [
                # To update the following tree view when there are modifications
                [self.env.ref("g2p_programs.view_cycle_tree").id, "tree"],
                [self.env.ref("g2p_program_claims.view_cycle_claims_form").id, "form"],
            ]
        return res
