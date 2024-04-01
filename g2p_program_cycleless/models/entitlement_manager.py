from odoo import _, models


class G2PEntitlementManagerDefault(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def open_entitlements_form(self, cycle):
        res = super().open_entitlements_form(cycle)
        program_dict = cycle.program_id.read()[0]
        if program_dict.get("is_reimbursement_program", False):
            res["name"] = _("Reimbursements")
        if program_dict.get("is_cycleless", False):
            res["name"] = _("Entitlements")
        return res
