from odoo import _, models


class G2PEntitlementManagerDefault(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def open_entitlements_form(self, cycle):
        res = super(G2PEntitlementManagerDefault, self).open_entitlements_form(cycle)
        if cycle.program_id.is_reimbursement_program:
            res["views"] = [
                [self.env.ref("g2p_programs.view_entitlement_tree").id, "tree"],
                [
                    self.env.ref(
                        "g2p_program_reimbursement.view_entitlement_reimbursement_form"
                    ).id,
                    "form",
                ],
            ]
            res["name"] = _("Reimbursements")
        return res
