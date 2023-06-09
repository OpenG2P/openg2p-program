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
            ("draft", "Applied"),
            ("duplicated", "In Progress"),
            ("enrolled", "In Progress"),
            ("not_eligible", "Not Eligible"),
            ("ent_approved", "In Progress"),
            ("again_enrolled", "In Progress"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
        ],
        compute="_compute_application_status",
        default="draft",
        store=True,
    )

    program_registrant_info = json_field.JSONField("Program Information", default={})

    program_membership_id = fields.Many2one(
        "g2p.program_membership", compute="_compute_program_membership", store=True
    )

    application_id = fields.Char(
        "Application ID", compute="_compute_application_id", store=True
    )

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

    @api.depends("program_membership_id.state", "program_membership_id.entitlement_ids")
    def _compute_application_status(self):
        for rec in self:

            entitlement = self.env["g2p.entitlement"].search(
                [
                    ("program_id", "=", rec.program_id.id),
                    ("partner_id", "=", rec.registrant_id.id),
                ]
            )

            if len(self.ids) == 1:
                if rec.program_membership_id.state == "draft":
                    rec.state = "draft"
                elif rec.program_membership_id.state == "not_eligible":
                    rec.state = "not_eligible"
                elif rec.program_membership_id.state == "duplicated":
                    rec.state = "duplicated"
                elif not entitlement and rec.program_membership_id.state == "enrolled":
                    rec.state = "enrolled"
                elif (
                    entitlement
                    and entitlement.state == "draft"
                    and rec.program_membership_id.state == "enrolled"
                ):
                    rec.state = "enrolled"
                elif (
                    entitlement
                    and entitlement.state == "approved"
                    and rec.program_membership_id.state == "enrolled"
                ):
                    rec.state = "ent_approved"
                elif (
                    entitlement
                    and entitlement.state == "approved"
                    and rec.program_membership_id.state == "enrolled"
                    and entitlement.show_print_voucher_button
                ):
                    rec.state = "completed"

                # TODO: Add reject status
                else:
                    rec.state = "rejected"

            else:
                rec.state = "again_enrolled"

                # TODO: Implement reject status in multiple submission also.

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
