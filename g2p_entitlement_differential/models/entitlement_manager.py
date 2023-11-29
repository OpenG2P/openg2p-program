# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class G2PCashEntitlementManager(models.Model):
    _inherit = "g2p.program.entitlement.manager.cash"

    inflation_rate = fields.Float()
    enable_inflation = fields.Boolean(default=False)

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

    def prepare_entitlements(self, cycle, beneficiaries):
        res = super().prepare_entitlements(cycle, beneficiaries)

        all_beneficiaries_ids = beneficiaries.mapped("partner_id.id")

        for ben in all_beneficiaries_ids:
            entitlement = self.env["g2p.entitlement"].search(
                [("partner_id", "=", ben), ("cycle_id", "=", cycle.id)]
            )
            if entitlement:
                if self.inflation_rate and self.enable_inflation:
                    entitlement.initial_amount = (
                        entitlement.initial_amount * self.inflation_rate
                    )

        return res

    def show_approve_entitlements(self, entitlement):
        # TODO: Enable the multi-stage entitlement approval
        return True


class G2PCashEntitlementItem(models.Model):
    _inherit = "g2p.program.entitlement.manager.cash.item"

    name = fields.Char()
