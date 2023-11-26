# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class EntitlementManager(models.Model):
    _inherit = "g2p.program.entitlement.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        cash_manager = ("g2p.program.entitlement.manager.cash", "Cash")
        if cash_manager in selection:
            selection[selection.index(cash_manager)] = (
                "g2p.program.entitlement.manager.cash",
                "Differential",
            )
        return selection


class G2PCashEntitlementManager(models.Model):
    _inherit = "g2p.program.entitlement.manager.cash"

    def _get_all_beneficiaries(
        self, all_beneficiaries_ids, condition, evaluate_one_item
    ):
        # res = super()._get_all_beneficiaries(all_beneficiaries_ids, condition, evaluate_one_item)
        domain = [("id", "in", all_beneficiaries_ids)]
        domain += self._safe_eval(condition)
        beneficiaries_ids = self.env["res.partner"].search(domain).ids
        if evaluate_one_item:
            return beneficiaries_ids
        return all_beneficiaries_ids


class G2PCashEntitlementItem(models.Model):
    _inherit = "g2p.program.entitlement.manager.cash.item"

    name = fields.Char()
