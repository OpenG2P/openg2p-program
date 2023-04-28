from odoo import _, models


class G2PEntitlementManagerDefault(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def open_entitlements_form(self, cycle):
        res = super(G2PEntitlementManagerDefault, self).open_entitlements_form(cycle)
        if cycle.program_id.is_claims_program:
            res["views"] = [
                [self.env.ref("g2p_programs.view_entitlement_tree").id, "tree"],
                [
                    self.env.ref("g2p_program_claims.view_entitlement_claim_form").id,
                    "form",
                ],
            ]
            if cycle.program_id.is_cycleless:
                res["name"] = _("Claims")
            else:
                res["name"] = _("Cycle Claims")
        return res
