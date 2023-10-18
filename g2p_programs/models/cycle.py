# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import json
import logging

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import constants

_logger = logging.getLogger(__name__)


class G2PCycle(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin", "job.relate.mixin"]
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

                send_payment_button = doc.xpath("//button[@name='send_payment']")
                send_payment_button[0].set("modifiers", modifiers)

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
    members_count = fields.Integer(string="# Beneficiaries", readonly=True)
    entitlements_count = fields.Integer(
        string="# Entitlements", readonly=True, compute="_compute_entitlements_count"
    )
    payments_count = fields.Integer(string="# Payments", readonly=True)

    # This is used to prevent any issue while some background tasks are happening such as importing beneficiaries
    locked = fields.Boolean(default=False)
    locked_reason = fields.Char()

    show_approve_entitlements_button = fields.Boolean(
        compute="_compute_show_approve_entitlement"
    )

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

    @api.onchange("entitlement_ids.state")
    def _compute_show_approve_entitlement(self):
        for rec in self:
            show_button = True
            for entitlement in rec.entitlement_ids:
                if entitlement.state != "approved":
                    show_button = False
                    break
            rec.show_approve_entitlements_button = show_button

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
        domain = [("cycle_id", "=", self.id)]
        if state:
            if isinstance(state, str):
                state = [state]
            domain += [("state", "in", state)]
        return self.env[entitlement_model].search(
            domain, offset=offset, limit=limit, order=order, count=count
        )

    # @api.model
    def copy_beneficiaries_from_program(self):
        # _logger.debug("Copying beneficiaries from program, cycles: %s", cycles)
        self.ensure_one()
        cycle_manager = self.program_id.get_manager(constants.MANAGER_CYCLE)
        if cycle_manager:
            return cycle_manager.copy_beneficiaries_from_program(self)
        else:
            raise UserError(_("No Cycle Manager defined."))

    def check_eligibility(self, beneficiaries=None):
        cycle_manager = self.program_id.get_manager(constants.MANAGER_CYCLE)

        if cycle_manager:
            cycle_manager.check_eligibility(self, beneficiaries)
        else:
            raise UserError(_("No Cycle Manager defined."))

    def to_approve(self):
        for rec in self:
            if rec.state == self.STATE_DRAFT:
                entitlement_manager = self.program_id.get_manager(
                    constants.MANAGER_ENTITLEMENT
                )
                if entitlement_manager:
                    rec.update({"state": self.STATE_TO_APPROVE})
                    entitlement_manager.set_pending_validation_entitlements(self)
                else:
                    raise UserError(_("No Entitlement Manager defined."))
            else:
                message = _("Ony 'draft' cycles can be set for approval.")
                kind = "danger"

                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Cycle"),
                        "message": message,
                        "sticky": False,
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
                        "sticky": False,
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
            if not cycle_manager:
                raise UserError(_("No Cycle Manager defined."))
            entitlement_manager = rec.program_id.get_manager(
                constants.MANAGER_ENTITLEMENT
            )
            if not entitlement_manager:
                raise UserError(_("No Entitlement Manager defined."))
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
        cycle_manager = self.program_id.get_manager(constants.MANAGER_CYCLE)
        if not cycle_manager:
            raise UserError(_("No Cycle Manager defined."))

        return cycle_manager.prepare_entitlements(self)

    def prepare_payment(self):
        # 1. Issue the payment of the beneficiaries using payment_manager.prepare_payments()
        payment_manager = self.program_id.get_manager(constants.MANAGER_PAYMENT)
        if not payment_manager:
            raise UserError(_("No Payment Manager defined."))

        return payment_manager.prepare_payments(self)

    def send_payment(self):
        # 1. Send the payments using payment_manager.send_payments()
        payment_manager = self.program_id.get_manager(constants.MANAGER_PAYMENT)
        if not payment_manager:
            raise UserError(_("No Payment Manager defined."))

        return payment_manager.send_payments(self.payment_batch_ids)

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
        entitlement_manager = self.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
        if not entitlement_manager:
            raise UserError(_("No Entitlement Manager defined."))

        return entitlement_manager.validate_entitlements(self)

    def export_distribution_list(self):
        # Not sure if this should be here.
        # It could be customizable reports based on https://github.com/OCA/reporting-engine
        pass

    def duplicate(self, new_start_date):
        # 1. Make sure the user has the right to do this
        # 2. Copy the cycle using the cycle manager
        pass

    def open_cycle_form(self):
        entitlement_manager = self.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
        payment_manager = self.program_id.get_manager(constants.MANAGER_PAYMENT)
        hide_cash = (
            False
            if entitlement_manager and entitlement_manager.IS_CASH_ENTITLEMENT
            else True
        )
        if not payment_manager:
            hide_cash = True

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
        entitlement_manager = self.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
        if entitlement_manager:
            return entitlement_manager.open_entitlements_form(self)
        else:
            raise UserError(_("No Entitlement Manager defined."))

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

    def refresh_page(self):
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def _get_related_job_domain(self):
        jobs = self.env["queue.job"].search([("model_name", "like", self._name)])
        related_jobs = jobs.filtered(lambda r: self in r.args[0])
        return [("id", "in", related_jobs.ids)]

    def unlink(self):
        for cycle in self:
            if cycle.state in ["approved"]:
                raise UserError(
                    _("Once a cycle has been approved, it cannot be deleted")
                )
            elif any(
                entitlement.state in ["approved"]
                for entitlement in cycle.entitlement_ids
            ):
                raise UserError(
                    _(
                        "A cycle for which entitlements have been approved cannot be deleted"
                    )
                )
            elif cycle.entitlement_ids:
                raise UserError(
                    _(
                        "Cycle cannot be deleted when Entitlements have been added to the cycle"
                    )
                )
            elif cycle.cycle_membership_ids:
                raise UserError(
                    _(
                        "Cycle cannot be deleted when beneficiaries are present in the cycle"
                    )
                )
            else:
                result = super(G2PCycle, cycle).unlink()
            return result
