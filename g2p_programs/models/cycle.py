# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import json
import logging

from lxml import etree

from odoo import _, api, fields, models

from . import constants

_logger = logging.getLogger(__name__)


class G2PCycle(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = "g2p.cycle"
    _description = "Cycle"
    _order = "sequence asc"
    _check_company_auto = True

    STATE_DRAFT = constants.STATE_DRAFT
    STATE_TO_APPROVE = constants.STATE_TO_APPROVE
    STATE_APPROVED = constants.STATE_APPROVED
    STATE_CANCELED = constants.STATE_CANCELLED
    STATE_DISTRIBUTED = constants.STATE_DISTRIBUTED
    STATE_ENDED = constants.STATE_ENDED

    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super(G2PCycle, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )

        if view_type == "form":
            # FIX: 'hide_cash' context is not set when form is loaded directly
            # via copy+paste URL in browser.
            # Set all payment management components to invisible
            # if the form was loaded directly via URL.
            if "hide_cash" not in self._context:
                doc = etree.XML(res["arch"])
                modifiers = json.dumps({"invisible": True})

                prepare_payment_button = doc.xpath("//button[@name='prepare_payment']")
                prepare_payment_button[0].set("modifiers", modifiers)
                open_payments_form_button = doc.xpath(
                    "//button[@name='open_payments_form']"
                )
                open_payments_form_button[0].set("modifiers", modifiers)
                payment_batches_page = doc.xpath("//page[@name='payment_batches']")
                payment_batches_page[0].set("modifiers", modifiers)

                res["arch"] = etree.tostring(doc, encoding="unicode")
        return res

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    program_id = fields.Many2one("g2p.program", "Program", required=True)
    sequence = fields.Integer(required=True, readonly=True, default=1)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    state = fields.Selection(
        [
            (STATE_DRAFT, "Draft"),
            (STATE_TO_APPROVE, "To Approve"),
            (STATE_APPROVED, "Approved"),
            (STATE_DISTRIBUTED, "Distributed"),
            (STATE_CANCELED, "Canceled"),
            (STATE_ENDED, "Ended"),
        ],
        default="draft",
    )

    cycle_membership_ids = fields.One2many(
        "g2p.cycle.membership", "cycle_id", "Cycle Memberships"
    )
    entitlement_ids = fields.One2many("g2p.entitlement", "cycle_id", "Entitlements")
    payment_batch_ids = fields.One2many(
        "g2p.payment.batch", "cycle_id", "Payment Batches"
    )

    # Get the auto-approve entitlement setting from the cycle manager
    auto_approve_entitlements = fields.Boolean("Auto-approve entitlements")

    # Statistics
    members_count = fields.Integer(string="# Beneficiaries")
    entitlements_count = fields.Integer(string="# Entitlements")
    payments_count = fields.Integer(string="# Payments")

    # This is used to prevent any issue while some background tasks are happening such as importing beneficiaries
    locked = fields.Boolean(default=False)
    locked_reason = fields.Char()

    def _compute_members_count(self):
        for rec in self:
            domain = rec._get_beneficiaries_domain(["enrolled"])
            members_count = self.env["g2p.cycle.membership"].search_count(domain)
            rec.update({"members_count": members_count})

    def _compute_entitlements_count(self):
        for rec in self:
            entitlements_count = self.env["g2p.entitlement"].search_count(
                [("cycle_id", "=", rec.id)]
            )
            rec.update({"entitlements_count": entitlements_count})

    def _compute_payments_count(self):
        for rec in self:
            payments_count = self.env["g2p.payment"].search_count(
                [("cycle_id", "=", rec.id)]
            )
            rec.update({"payments_count": payments_count})

    @api.onchange("start_date")
    def on_start_date_change(self):
        self.program_id.get_manager(constants.MANAGER_CYCLE).on_start_date_change(self)

    @api.onchange("state")
    def on_state_change(self):
        self.program_id.get_manager(constants.MANAGER_CYCLE).on_state_change(self)

    def _get_beneficiaries_domain(self, states=None):
        domain = [("cycle_id", "=", self.id)]
        if states:
            domain.append(("state", "in", states))
        return domain

    @api.model
    def get_beneficiaries(self, state, offset=0, limit=None, order=None, count=False):
        if isinstance(state, str):
            state = [state]
        for rec in self:
            domain = rec._get_beneficiaries_domain(state)
            return self.env["g2p.cycle.membership"].search(
                domain, offset=offset, limit=limit, order=order, count=count
            )

    def get_entitlements(
        self,
        state,
        entitlement_model="g2p.entitlement",
        offset=0,
        limit=None,
        order=None,
        count=False,
    ):
        """
        Query entitlements based on state
        :param state: List of states
        :param entitlement_model: String value of entitlement model to search
        :param offset: Optional integer value for the ORM search offset
        :param limit: Optional integer value for the ORM search limit
        :param order: Optional string value for the ORM search order fields
        :param count: Optional boolean for executing a search-count (if true) or search (if false: default)
        :return:
        """
        if isinstance(state, str):
            state = [state]
        domain = [("cycle_id", "=", self.id), ("state", "in", state)]
        return self.env[entitlement_model].search(
            domain, offset=offset, limit=limit, order=order, count=count
        )

    # @api.model
    def copy_beneficiaries_from_program(self):
        # _logger.debug("Copying beneficiaries from program, cycles: %s", cycles)
        self.ensure_one()
        return self.program_id.get_manager(
            constants.MANAGER_CYCLE
        ).copy_beneficiaries_from_program(self)

    def check_eligibility(self, beneficiaries=None):
        self.program_id.get_manager(constants.MANAGER_CYCLE).check_eligibility(
            self, beneficiaries
        )

    def to_approve(self):
        for rec in self:
            if rec.state == self.STATE_DRAFT:
                rec.update({"state": self.STATE_TO_APPROVE})
                self.program_id.get_manager(
                    constants.MANAGER_ENTITLEMENT
                ).set_pending_validation_entitlements(self)
            else:
                message = _("Ony 'draft' cycles can be set for approval.")
                kind = "danger"

                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Cycle"),
                        "message": message,
                        "sticky": True,
                        "type": kind,
                        "next": {
                            "type": "ir.actions.act_window_close",
                        },
                    },
                }

    def reset_draft(self):
        for rec in self:
            if rec.state == self.STATE_TO_APPROVE:
                rec.update({"state": self.STATE_DRAFT})
            else:
                message = _("Ony 'to approve' cycles can be reset to draft.")
                kind = "danger"

                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Cycle"),
                        "message": message,
                        "sticky": True,
                        "type": kind,
                        "next": {
                            "type": "ir.actions.act_window_close",
                        },
                    },
                }

    def approve(self):
        # 1. Make sure the user has the right to do this
        # 2. Approve the cycle using the cycle manager
        for rec in self:
            cycle_manager = rec.program_id.get_manager(constants.MANAGER_CYCLE)
            entitlement_manager = rec.program_id.get_manager(
                constants.MANAGER_ENTITLEMENT
            )
            return cycle_manager.approve_cycle(
                rec,
                auto_approve=cycle_manager.auto_approve_entitlements,
                entitlement_manager=entitlement_manager,
            )

    def notify_cycle_started(self):
        # 1. Notify the beneficiaries using notification_manager.cycle_started()
        pass

    def prepare_entitlement(self):
        # 1. Prepare the entitlement of the beneficiaries using entitlement_manager.prepare_entitlements()
        self.program_id.get_manager(constants.MANAGER_CYCLE).prepare_entitlements(self)

    def prepare_payment(self):
        # 1. Issue the payment of the beneficiaries using payment_manager.prepare_payments()
        return self.program_id.get_manager(constants.MANAGER_PAYMENT).prepare_payments(
            self
        )

    def mark_distributed(self):
        # 1. Mark the cycle as distributed using the cycle manager
        self.program_id.get_manager(constants.MANAGER_CYCLE).mark_distributed(self)

    def mark_ended(self):
        # 1. Mark the cycle as ended using the cycle manager
        self.program_id.get_manager(constants.MANAGER_CYCLE).mark_ended(self)

    def mark_cancelled(self):
        # 1. Mark the cycle as cancelled using the cycle manager
        self.program_id.get_manager(constants.MANAGER_CYCLE).mark_cancelled(self)

    def validate_entitlement(self):
        # 1. Make sure the user has the right to do this
        # 2. Validate the entitlement of the beneficiaries using entitlement_manager.validate_entitlements()
        return self.program_id.get_manager(
            constants.MANAGER_ENTITLEMENT
        ).validate_entitlements(self)

    def export_distribution_list(self):
        # Not sure if this should be here.
        # It could be customizable reports based on https://github.com/OCA/reporting-engine
        pass

    def duplicate(self, new_start_date):
        # 1. Make sure the user has the right to do this
        # 2. Copy the cycle using the cycle manager
        pass

    def open_cycle_form(self):
        is_cash_entitlement = self.program_id.get_manager(
            constants.MANAGER_ENTITLEMENT
        ).IS_CASH_ENTITLEMENT
        hide_cash = True
        if is_cash_entitlement:
            hide_cash = False

        return {
            "name": "Cycle",
            "view_mode": "form",
            "res_model": "g2p.cycle",
            "res_id": self.id,
            "view_id": self.env.ref("g2p_programs.view_cycle_form").id,
            "type": "ir.actions.act_window",
            "context": {"hide_cash": hide_cash},
            "target": "current",
            "flags": {"mode": "readonly"},
        }

    def open_members_form(self):
        self.ensure_one()

        action = {
            "name": _("Cycle Members"),
            "type": "ir.actions.act_window",
            "res_model": "g2p.cycle.membership",
            "context": {
                "create": False,
                "default_cycle_id": self.id,
                "search_default_enrolled_state": 1,
            },
            "view_mode": "list,form",
            "domain": [("cycle_id", "=", self.id)],
        }
        return action

    def open_entitlements_form(self):
        return self.program_id.get_manager(
            constants.MANAGER_ENTITLEMENT
        ).open_entitlements_form(self)

    def open_payments_form(self):
        self.ensure_one()

        action = {
            "name": _("Payments"),
            "type": "ir.actions.act_window",
            "res_model": "g2p.payment",
            "context": {
                "create": False,
            },
            "view_mode": "list,form",
            "domain": [("entitlement_id", "in", self.entitlement_ids.ids)],
        }
        return action
