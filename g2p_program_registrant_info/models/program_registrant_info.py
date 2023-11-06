# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import random
from datetime import datetime

from odoo import api, fields, models

from odoo.addons.g2p_json_field.models import json_field


class G2PProgramRegistrantInfo(models.Model):
    _name = "g2p.program.registrant_info"
    _description = "Program Registrant Info"
    _order = "id desc"

    registrant_id = fields.Many2one(
        "res.partner",
        help="A beneficiary",
        required=False,
        auto_join=True,
        # ondelete='set null'
    )
    program_id = fields.Many2one(
        "g2p.program",
        help="A program",
        required=False,
        auto_join=True,
        # ondelete='set null'
    )

    state = fields.Selection(
        [
            ("active", "Applied"),
            ("inprogress", "In Progress"),
            ("rejected", "Rejected"),
            ("completed", "Completed"),
            ("closed", "Closed"),
        ],
        default="active",
    )

    program_registrant_info = json_field.JSONField("Program Information", default={})

    program_membership_id = fields.Many2one(
        "g2p.program_membership", compute="_compute_program_membership", store=True
    )

    application_id = fields.Char(
        "Application ID", compute="_compute_application_id", store=True
    )

    entitlement_id = fields.Many2one("g2p.entitlement")

    sl_no = fields.Integer(string="SNo.", compute="_compute_sl_no")

    def _compute_sl_no(self):
        sl_no = 0
        for record in self:
            sl_no += 1
            record.sl_no = sl_no

    @api.depends("registrant_id", "program_id")
    def _compute_program_membership(self):
        for rec in self:
            result = self.env["g2p.program_membership"].search(
                [
                    ("registrant_id", "=", rec.registrant_id.id),
                    ("program_id", "=", rec.program_id.id),
                ]
            )
            if len(result) > 0:
                rec.program_membership_id = result[0]
            else:
                rec.program_membership_id = None

    @api.depends("registrant_id", "program_id")
    def _compute_application_id(self):
        for rec in self:
            d = datetime.today().strftime("%d")
            m = datetime.today().strftime("%m")
            y = datetime.today().strftime("%y")

            random_number = str(random.randint(1, 100000))

            rec.application_id = d + m + y + random_number.zfill(5)

    def open_registrant_form(self):
        return {
            "name": "Program Registrant Info",
            "view_mode": "form",
            "res_model": "g2p.program.registrant_info",
            "res_id": self.id,
            "view_id": self.env.ref(
                "g2p_program_registrant_info.view_program_registrant_info_form"
            ).id,
            "type": "ir.actions.act_window",
            "target": "new",
            "flags": {"mode": "readonly"},
        }

    @api.model
    def trigger_latest_status_of_entitlement(self, entitlement, state, check_states=()):
        if entitlement:
            reg_info = entitlement.latest_registrant_info
            if reg_info:
                if (not check_states) or (reg_info.state in check_states):
                    reg_info.state = state
                    return True
        return False

    @api.model
    def trigger_latest_status_membership(
        self, program_membership, state, check_states=()
    ):
        if program_membership:
            reg_info = program_membership.latest_registrant_info
            if reg_info:
                if (not check_states) or (reg_info.state in check_states):
                    reg_info.state = state
                    return True
        return False

    @api.model
    def assign_reg_info_to_entitlement_from_membership(self, entitlement):
        membership = entitlement.partner_id.program_membership_ids.filtered(
            lambda x: x.program_id.id == entitlement.program_id.id
        )
        reg_info = membership.latest_registrant_info
        if reg_info:
            reg_info.entitlement_id = entitlement

    @api.model
    def reject_entitlement_for_membership(
        self, program_membership, reject_state="rejected3"
    ):
        if program_membership:
            reg_info = program_membership.latest_registrant_info
            if reg_info and reg_info.entitlement_id:
                reg_info.entitlement_id.state = reject_state

    def open_new_tab(self):
        return {
            "name": "Record View",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "target": "new",
            "flags": {"mode": "readonly"},
            "context": {"create": False, "edit": False},
        }
