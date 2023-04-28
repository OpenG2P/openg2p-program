from odoo import _, models


class G2PEntitlementManagerDefault(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def open_entitlements_form(self, cycle):
        res = super(G2PEntitlementManagerDefault, self).open_entitlements_form(cycle)
        if cycle.program_id.is_cycleless:
            res["name"] = _("Entitlements")
        return res
