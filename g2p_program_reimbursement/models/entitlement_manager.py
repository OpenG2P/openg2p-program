from odoo import models


class G2PEntitlementManagerDefault(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def open_entitlements_form(self, cycle):
        res = super(G2PEntitlementManagerDefault, self).open_entitlements_form(cycle)
        if cycle.program_id.is_reimbursement_program:
            # TODO: Reloading on reimbursement tree view will blank out the page
            # because of the following context not being available.
            action = self.env.ref(
                "g2p_program_reimbursement.action_reimbursement"
            ).read()[0]
            action["context"] = {"default_cycle_id": cycle.id}
            return action
        return res
