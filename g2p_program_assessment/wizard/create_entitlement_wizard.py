# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class G2PEntitlementWizard(models.TransientModel):
    _name = "g2p.entitlement.create.wizard"
    _description = "G2P Entitlement Create Wizard"

    name = fields.Char()
    partner_id = fields.Many2one(
        "res.partner",
        "Registrant",
        help="A beneficiary",
        required=True,
        domain=[("is_registrant", "=", True)],
    )
    cycle_id = fields.Many2one("g2p.cycle", required=True)
    program_id = fields.Many2one("g2p.program")

    valid_from = fields.Date()
    valid_until = fields.Date()

    currency_id = fields.Many2one("res.currency")

    initial_amount = fields.Monetary(required=True, currency_field="currency_id")
    transfer_fee = fields.Monetary(default=0.0, currency_field="currency_id")

    @api.model
    def open_entitlement_form_wizard(self, beneficiary):
        # TODO: Consider create wizard with multiple beneficiaries
        beneficiary.ensure_one()

        program = beneficiary.program_id
        active_cycle = None
        show_cycle_id = False

        is_cycleless = program.read()[0].get("is_cycleless", False)
        if is_cycleless:
            active_cycle = program.default_active_cycle
            show_cycle_id = True
            # TODO: Analyze cycle end date logic when cycleless
            valid_from = datetime.utcnow()
            valid_until = valid_from + (active_cycle.end_date - active_cycle.start_date)
        else:
            active_cycle = (
                program.cycle_ids.filtered(lambda x: x.state == "draft").sorted(
                    "start_date", reverse=True
                )[0]
                if program.cycle_ids.filtered(lambda x: x.state == "draft")
                else None
            )
            if not active_cycle:
                raise UserError(
                    _("No cycle is present for program: %s. Create a new cycle.")
                    % program.name
                )
            valid_from = active_cycle.start_date
            valid_until = active_cycle.end_date

        return {
            "name": "Create Entitlement",
            "type": "ir.actions.act_window",
            "res_model": "g2p.entitlement.create.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": beneficiary.partner_id.id,
                "default_program_id": beneficiary.program_id.id,
                "default_currency_id": beneficiary.program_id.journal_id.currency_id.id,
                "default_cycle_id": active_cycle.id if active_cycle else None,
                "default_valid_from": valid_from,
                "default_valid_until": valid_until,
                "show_cycle_id": show_cycle_id,
            },
        }

    def create_entitlement(self):
        if not self.initial_amount or self.initial_amount <= 0:
            raise ValidationError(_("Amount cannot be zero or empty or negative."))

        existing_entitlements_count = self.env["g2p.entitlement"].search_count(
            [
                ("partner_id", "=", self.partner_id.id),
                ("program_id", "=", self.program_id.id),
                ("cycle_id", "=", self.cycle_id.id),
                ("state", "=", "draft"),
            ]
        )
        if existing_entitlements_count:
            raise ValidationError(
                _("Entitlement already exists. Approve/Edit the existing entitlement.")
            )

        # TODO: Find a way to reuse entitlement_manager.prepare_entitlements
        entitlement = self.env["g2p.entitlement"].create(
            self.generate_create_entitlement_dict()
        )
        entitlement.copy_assessments_from_beneficiary()
        try:
            entitlement.copy_documents_from_beneficiary()
        except Exception as e:
            _logger.warning("Prgram Documents Module is not installed. %s", e)
        try:
            self.env[
                "g2p.program.registrant_info"
            ].trigger_latest_status_of_entitlement(
                entitlement, "inprogress", check_states=("active",)
            )
            self.env[
                "g2p.program.registrant_info"
            ].assign_reg_info_to_entitlement_from_membership(entitlement)
        except Exception as e:
            _logger.warning("Prgram Registrant Info Module not installed. %s", e)
        message = _("Entitlement created.")
        kind = "success"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Entitlement"),
                "message": message,
                "sticky": False,
                "type": kind,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }

    def generate_create_entitlement_dict(self):
        if self:
            self.ensure_one()
            return {
                "cycle_id": self.cycle_id.id,
                "partner_id": self.partner_id.id,
                "initial_amount": self.initial_amount,
                "transfer_fee": self.transfer_fee,
                "state": "draft",
                "is_cash_entitlement": True,
                "valid_from": self.valid_from,
                "valid_until": self.valid_until,
            }
        return {}
