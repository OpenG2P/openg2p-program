# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class G2PCashEntitlementManager(models.Model):
    _inherit = "g2p.program.entitlement.manager.cash"

    inflation_rate = fields.Float()
    enable_inflation = fields.Boolean(default=False)

    def _get_all_beneficiaries(self, all_beneficiaries_ids, condition, evaluate_one_item):
        # res = super()._get_all_beneficiaries(all_beneficiaries_ids, condition, evaluate_one_item)
        domain = [("id", "in", all_beneficiaries_ids)]
        domain += self._safe_eval(condition)
        beneficiaries_ids = self.env["res.partner"].search(domain).ids
        if evaluate_one_item:
            return beneficiaries_ids
        return all_beneficiaries_ids

    def prepare_entitlements(self, cycle, beneficiaries):  # noqa: C901
        # NOTE: This method is an enriched implementation of the prepare_entitlements method
        #       from spp_entitlement_cash (by OpenSPP):
        #       <https://github.com/OpenSPP/openspp-modules/tree/17.0/spp_entitlement_cash>

        # TODO: Refactor this method once a dedicated _compute_entitlement_amount method is introduced.
        if not self.entitlement_item_ids:
            raise UserError(_("There are no items entered for this entitlement manager."))

        all_beneficiaries_ids = beneficiaries.mapped("partner_id.id")

        new_entitlements_to_create = {}
        for rec in self.entitlement_item_ids:
            _logger.info(f"Rec Amount: {rec.amount}")
            if rec.condition:
                beneficiaries_ids = self._get_all_beneficiaries(
                    all_beneficiaries_ids, rec.condition, self.evaluate_one_item
                )
            else:
                beneficiaries_ids = all_beneficiaries_ids
            _logger.info(f"Beneficiaries IDs: {beneficiaries_ids}")

            beneficiaries_with_entitlements = (
                self.env["g2p.entitlement"]
                .search(
                    [
                        ("cycle_id", "=", cycle.id),
                        ("partner_id", "in", beneficiaries_ids),
                    ]
                )
                .mapped("partner_id.id")
            )
            entitlements_to_create = [
                beneficiaries_id
                for beneficiaries_id in beneficiaries_ids
                if beneficiaries_id not in beneficiaries_with_entitlements
            ]

            entitlement_start_validity = cycle.start_date
            entitlement_end_validity = cycle.end_date
            entitlement_currency = rec.currency_id.id

            beneficiaries_with_entitlements_to_create = self.env["res.partner"].browse(entitlements_to_create)

            for beneficiary_id in beneficiaries_with_entitlements_to_create:
                if rec.multiplier_field:
                    # Get the multiplier value from multiplier_field else return the default multiplier=1
                    multiplier = beneficiary_id.mapped(rec.multiplier_field.name)
                    if multiplier:
                        multiplier = multiplier[0] or 0
                else:
                    multiplier = 1
                if rec.max_multiplier > 0 and multiplier > rec.max_multiplier:
                    multiplier = rec.max_multiplier
                _logger.info(f"Multiplier: {multiplier}")

                amount = 0.0
                if rec.amount_type == "dynamic_field":
                    if not rec.amount_field:
                        raise UserError(_("Amount Field can't be empty in case of Dynamic Field Amount Type"))
                    else:
                        amount_field = beneficiary_id.mapped(rec.amount_field.name)
                        if amount_field:
                            amount_field = amount_field[0] or 0
                        amount = float(amount_field) * float(multiplier)
                else:
                    amount = rec.amount * float(multiplier)

                # Compute the sum of cash entitlements
                if beneficiary_id.id in new_entitlements_to_create:
                    amount = amount + new_entitlements_to_create[beneficiary_id.id]["initial_amount"]
                # Check if amount > max_amount; ignore if max_amount is set to 0
                if self.max_amount > 0.0 and amount > self.max_amount:
                    amount = self.max_amount

                new_entitlements_to_create[beneficiary_id.id] = {
                    "cycle_id": cycle.id,
                    "partner_id": beneficiary_id.id,
                    "initial_amount": amount,
                    "currency_id": entitlement_currency,
                    "state": "draft",
                    "is_cash_entitlement": True,
                    "valid_from": entitlement_start_validity,
                    "valid_until": entitlement_end_validity,
                }
                # Check if there are additional fields to be added in entitlements
                addl_fields = self._get_addl_entitlement_fields(beneficiary_id)
                if addl_fields:
                    new_entitlements_to_create[beneficiary_id.id].update(addl_fields)

        # Create entitlement records
        for ent in new_entitlements_to_create:
            initial_amount = new_entitlements_to_create[ent]["initial_amount"]
            new_entitlements_to_create[ent]["initial_amount"] = self._check_subsidy(initial_amount)
            if self.inflation_rate and self.enable_inflation:
                new_entitlements_to_create[ent]["initial_amount"] = (
                    new_entitlements_to_create[ent]["initial_amount"] * self.inflation_rate
                )

            # Create non-zero entitlements only
            if new_entitlements_to_create[ent]["initial_amount"] > 0.0:
                self.env["g2p.entitlement"].create(new_entitlements_to_create[ent])

    def show_approve_entitlements(self, entitlement):
        # TODO: Enable the multi-stage entitlement approval
        return True


class G2PCashEntitlementItem(models.Model):
    _inherit = "g2p.program.entitlement.manager.cash.item"

    name = fields.Char()

    amount_type = fields.Selection(
        [("constant", "Constant"), ("dynamic_field", "Dynamic Field")], default="constant", required=True
    )
    amount_field = fields.Many2one(
        "ir.model.fields",
        domain=[("model_id.model", "=", "res.partner"), ("ttype", "=", "integer")],
    )

    @api.onchange("amount_type")
    def onchange_amount_type(self):
        if self.amount_type == "dynamic_field":
            self.amount = 0.0
        else:
            self.amount_field = None
