# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EntitlementManager(models.Model):
    _name = "g2p.program.entitlement.manager"
    _description = "Entitlement Manager"
    _inherit = "g2p.manager.mixin"

    program_id = fields.Many2one("g2p.program", "Program")

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = ("g2p.program.entitlement.manager.default", "Default")
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class BaseEntitlementManager(models.AbstractModel):
    _name = "g2p.base.program.entitlement.manager"
    _inherit = "base.programs.manager"
    _description = "Base Entitlement Manager"

    name = fields.Char("Manager Name", required=True)
    program_id = fields.Many2one("g2p.program", string="Program", required=True)

    def prepare_entitlements(self, cycle, cycle_memberships):
        """
        This method is used to prepare the entitlement list of the beneficiaries.
        :param cycle: The cycle.
        :param cycle_memberships: The beneficiaries.
        :return:
        """
        raise NotImplementedError()

    def validate_entitlements(self, cycle, cycle_memberships):
        """
        This method is used to validate the entitlement list of the beneficiaries.
        :param cycle: The cycle.
        :param cycle_memberships: The beneficiaries.
        :return:
        """
        raise NotImplementedError()

    def approve_entitlements(self, entitlements):
        """
        This method is used to approve the entitlement list of the beneficiaries.
        :param cycle: The cycle.
        :param cycle_memberships: The beneficiaries.
        :return:
        """
        raise NotImplementedError()

    def is_cash_entitlement(self):
        return False

    def check_fund_balance(self, program_id):
        company_id = self.env.user.company_id and self.env.user.company_id.id or None
        retval = 0.0
        if company_id:
            params = (
                company_id,
                program_id,
            )

            # Get the current fund balance
            fund_bal = 0.0
            sql = """
                select sum(amount) as total_fund
                from g2p_program_fund
                where company_id = %s
                    AND program_id = %s
                    AND state = 'posted'
                """
            self._cr.execute(sql, params)
            program_funds = self._cr.dictfetchall()
            fund_bal = program_funds[0]["total_fund"] or 0.0

            # Get the current entitlement totals
            total_entitlements = 0.0
            sql = """
                select sum(a.initial_amount) as total_entitlement
                from g2p_entitlement a
                    left join g2p_cycle b on b.id = a.cycle_id
                where a.company_id = %s
                    AND b.program_id = %s
                    AND a.state = 'approved'
                """
            self._cr.execute(sql, params)
            entitlements = self._cr.dictfetchall()
            total_entitlements = entitlements[0]["total_entitlement"] or 0.0

            retval = fund_bal - total_entitlements
        return retval


class DefaultCashEntitlementManager(models.Model):
    _name = "g2p.program.entitlement.manager.default"
    _inherit = ["g2p.base.program.entitlement.manager", "g2p.manager.source.mixin"]
    _description = "Default Entitlement Manager"

    amount_per_cycle = fields.Monetary(
        currency_field="currency_id",
        group_operator="sum",
        default=0.0,
    )
    amount_per_individual_in_group = fields.Monetary(
        currency_field="currency_id",
        group_operator="sum",
        default=0.0,
    )
    max_individual_in_group = fields.Integer(
        default=0,
        string="Maximum number of individual in group",
        help="0 means no limit",
    )

    currency_id = fields.Many2one(
        "res.currency", related="program_id.journal_id.currency_id", readonly=True
    )

    # Transfer Fees
    transfer_fee_pct = fields.Float(
        "Transfer Fee(%)",
        decimal=(5, 2),
        default=0.0,
        help="Transfer fee will be a percentage of amount",
    )
    transfer_fee_amt = fields.Monetary(
        "Transfer Fee Amount",
        default=0.0,
        currency_field="currency_id",
        help="Set fixed transfer fee amount",
    )

    # Group able to validate the payment
    # Todo: Create a record rule for payment_validation_group
    entitlement_validation_group_id = fields.Many2one(
        "res.groups", string="Entitlement Validation Group"
    )

    @api.onchange("transfer_fee_pct")
    def on_transfer_fee_pct_change(self):
        if self.transfer_fee_pct > 0.0:
            self.transfer_fee_amt = 0.0

    @api.onchange("transfer_fee_amt")
    def on_transfer_fee_amt_change(self):
        if self.transfer_fee_amt > 0.0:
            self.transfer_fee_pct = 0.0

    def prepare_entitlements(self, cycle, beneficiaries):
        # TODO: create a Entitlement of `amount_per_cycle` for each member that do not have one yet for the cycle and
        benecifiaries_ids = beneficiaries.mapped("partner_id.id")

        benecifiaries_with_entitlements = (
            self.env["g2p.entitlement"]
            .search(
                [("cycle_id", "=", cycle.id), ("partner_id", "in", benecifiaries_ids)]
            )
            .mapped("partner_id.id")
        )
        entitlements_to_create = [
            benecifiaries_id
            for benecifiaries_id in benecifiaries_ids
            if benecifiaries_id not in benecifiaries_with_entitlements
        ]

        entitlement_start_validity = cycle.start_date
        entitlement_end_validity = cycle.end_date
        entitlement_currency = self.currency_id.id

        beneficiaries_with_entitlements_to_create = self.env["res.partner"].browse(
            entitlements_to_create
        )

        for beneficiary_id in beneficiaries_with_entitlements_to_create:
            amount = self._calculate_amount(beneficiary_id)
            transfer_fee = 0.0
            if self.transfer_fee_pct > 0.0:
                transfer_fee = amount * (self.transfer_fee_pct / 100.0)
            elif self.transfer_fee_amt > 0.0:
                transfer_fee = self.transfer_fee_amt
            self.env["g2p.entitlement"].create(
                {
                    "cycle_id": cycle.id,
                    "partner_id": beneficiary_id.id,
                    "initial_amount": amount,
                    "transfer_fee": transfer_fee,
                    "currency_id": entitlement_currency,
                    "state": "draft",
                    "is_cash_entitlement": True,
                    "valid_from": entitlement_start_validity,
                    "valid_until": entitlement_end_validity,
                }
            )

    def _calculate_amount(self, beneficiary):
        total = self.amount_per_cycle
        if beneficiary.is_group:
            num_individuals = beneficiary.count_individuals()
            if num_individuals:
                result_map = dict(num_individuals)
                num_individuals = result_map.get(beneficiary.id, 0)
                # if (
                #    self.max_individual_in_group
                #    and num_individuals > self.max_individual_in_group
                # ):
                #    num_individuals = self.max_individual_in_group
                if self.max_individual_in_group:
                    num_individuals = min(num_individuals, self.max_individual_in_group)

                total += self.amount_per_individual_in_group * float(num_individuals)
        return total

    def validate_entitlements(self, cycle, cycle_memberships):
        # TODO: Change the status of the entitlements to `validated` for this members.
        # move the funds from the program's wallet to the wallet of each Beneficiary that are validated
        pass

    def is_cash_entitlement(self):
        return True

    def approve_entitlements(self, entitlements):
        amt = 0.0
        state_err = 0
        message = ""
        sw = 0
        for rec in entitlements:
            if rec.state in ("draft", "pending_validation"):
                fund_balance = self.check_fund_balance(rec.cycle_id.program_id.id) - amt
                if fund_balance >= rec.initial_amount:
                    amt += rec.initial_amount
                    # Prepare journal entry (account.move) via account.payment
                    amount = rec.initial_amount
                    new_service_fee = None
                    if rec.transfer_fee > 0.0:
                        amount -= rec.transfer_fee
                        # Incurred Fees (transfer fees)
                        payment = {
                            "partner_id": rec.partner_id.id,
                            "payment_type": "outbound",
                            "amount": rec.transfer_fee,
                            "currency_id": rec.journal_id.currency_id.id,
                            "journal_id": rec.journal_id.id,
                            "partner_type": "supplier",
                            "ref": "Service Fee: Code: %s" % rec.code,
                        }
                        new_service_fee = self.env["account.payment"].create(payment)

                    # Fund Disbursed (amount - transfer fees)
                    payment = {
                        "partner_id": rec.partner_id.id,
                        "payment_type": "outbound",
                        "amount": amount,
                        "currency_id": rec.journal_id.currency_id.id,
                        "journal_id": rec.journal_id.id,
                        "partner_type": "supplier",
                        "ref": "Fund disbursed to beneficiary: Code: %s" % rec.code,
                    }
                    new_payment = self.env["account.payment"].create(payment)

                    rec.update(
                        {
                            "disbursement_id": new_payment.id,
                            "service_fee_disbursement_id": new_service_fee
                            and new_service_fee.id
                            or None,
                            "state": "approved",
                            "date_approved": fields.Date.today(),
                        }
                    )
                else:
                    raise UserError(
                        _(
                            "The fund for the program: %(program)s [%(fund).2f] "
                            + "is insufficient for the entitlement: %(entitlement)s"
                        )
                        % {
                            "program": rec.cycle_id.program_id.name,
                            "fund": fund_balance,
                            "entitlement": rec.code,
                        }
                    )
                # _logger.info("DEBUG: approve_entitlements: amt2: %s", amt)

            else:
                state_err += 1
                if sw == 0:
                    sw = 1
                    message = _(
                        "<b>Entitlement State Error! Entitlements not in 'pending validation' state:</b>\n"
                    )
                message += _("Program: %(prg)s, Beneficiary: %(partner)s.\n") % {
                    "prg": rec.cycle_id.program_id.name,
                    "partner": rec.partner_id.name,
                }

        return (state_err, message)

    def open_entitlement_form(self, rec):
        return {
            "name": "Entitlement",
            "view_mode": "form",
            "res_model": "g2p.entitlement",
            "res_id": rec.id,
            "view_id": self.env.ref("g2p_programs.view_entitlement_form").id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
