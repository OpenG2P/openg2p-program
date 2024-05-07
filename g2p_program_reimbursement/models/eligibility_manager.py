from odoo import models


class G2PDefaultEligibilityManager(models.Model):
    _inherit = "g2p.program_membership.manager.default"

    def _prepare_eligible_domain(self, membership=None):
        domain = super()._prepare_eligible_domain(membership)
        if self.env.context.get("is_reimbursement_program"):
            domain = []
            domain = [
                ("supplier_rank", ">", 0),
                ("is_group", "=", False),
                ("is_registrant", "=", False),
            ]
            return domain
        return domain
