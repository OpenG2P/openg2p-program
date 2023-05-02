# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import random
from datetime import datetime

from lxml import etree

from odoo import api, fields, models

from . import constants


class G2PProgramMembership(models.Model):
    _name = "g2p.program_membership"
    _description = "Program Membership"
    _order = "id desc"

    partner_id = fields.Many2one(
        "res.partner",
        "Registrant",
        help="A beneficiary",
        required=True,
        auto_join=True,
        domain=[("is_registrant", "=", True)],
    )
    program_id = fields.Many2one(
        "g2p.program", "", help="A program", required=True, auto_join=True
    )

    # TODO: When the state is changed from "exited", "not_eligible" or "duplicate" to something else
    #      then reset the deduplication date.
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("enrolled", "Enrolled"),
            ("paused", "Paused"),
            ("exited", "Exited"),
            ("not_eligible", "Not Eligible"),
            ("duplicated", "Duplicated"),
        ],
        default="draft",
        copy=False,
    )

    enrollment_date = fields.Date(default=lambda self: fields.Datetime.now())
    last_deduplication = fields.Date("Last Deduplication Date")
    exit_date = fields.Date()

    application_id = fields.Char(
        "Application ID", compute="_compute_application_id", store=True
    )

    registrant_id = fields.Integer(string="Registrant ID", related="partner_id.id")
    address = fields.Text(related="partner_id.address")
    email = fields.Char(related="partner_id.email")
    phone = fields.Char(related="partner_id.phone")
    phone_number_ids = fields.One2many(related="partner_id.phone_number_ids")
    birthdate = fields.Date(related="partner_id.birthdate")
    age = fields.Char(related="partner_id.age")
    birth_place = fields.Char(related="partner_id.birth_place")
    gender = fields.Selection(related="partner_id.gender")
    bank_ids = fields.One2many(related="partner_id.bank_ids")
    reg_ids = fields.One2many(related="partner_id.reg_ids")
    related_1_ids = fields.One2many(related="partner_id.related_1_ids")
    related_2_ids = fields.One2many(related="partner_id.related_2_ids")
    is_registrant = fields.Boolean(
        related="partner_id.is_registrant", string="Is Registrant"
    )
    is_group = fields.Boolean(related="partner_id.is_group", string="Is Group")
    group_membership_ids = fields.One2many(related="partner_id.group_membership_ids")
    individual_membership_ids = fields.One2many(
        related="partner_id.individual_membership_ids"
    )
    program_membership_ids = fields.One2many(
        related="partner_id.program_membership_ids"
    )
    entitlement_ids = fields.One2many(related="partner_id.entitlement_ids")
    registration_date = fields.Date(related="partner_id.registration_date")

    _sql_constraints = [
        (
            "program_membership_unique",
            "unique (partner_id, program_id)",
            "Beneficiary must be unique per program.",
        ),
    ]

    # TODO: Implement exit reasons
    # exit_reason_id = fields.Many2one("Exit Reason") Default: Completed, Opt-Out, Other

    # TODO: Implement not eligible reasons
    # Default: "Missing data", "Does not match the criterias", "Duplicate", "Other"
    # not_eligible_reason_id = fields.Many2one("Not Eligible Reason")

    # TODO: Add a field delivery_mechanism_id
    # delivery_mechanism_id = fields.Many2one("Delivery mechanism type", help="Delivery mechanism")
    # the phone number, bank account, etc.
    delivery_mechanism_value = fields.Char()

    # TODO: JJ - Add a field for the preferred notification method

    deduplication_status = fields.Selection(
        selection=[
            ("new", "New"),
            ("processing", "Processing"),
            ("verified", "Verified"),
            ("duplicated", "duplicated"),
        ],
        default="new",
        copy=False,
    )

    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        context = self.env.context
        result = super(G2PProgramMembership, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == "form":
            update_arch = False
            doc = etree.XML(result["arch"])

            # Check if we need to change the partner_id domain filter
            target_type = context.get("target_type", False)
            if target_type:
                domain = None
                if context.get("target_type", False) == "group":
                    domain = "[('is_registrant', '=', True), ('is_group','=',True)]"
                elif context.get("target_type", False) == "individual":
                    domain = "[('is_registrant', '=', True), ('is_group','=',False)]"
                if domain:
                    update_arch = True
                    nodes = doc.xpath("//field[@name='partner_id']")
                    for node in nodes:
                        node.set("domain", domain)

            if update_arch:
                result["arch"] = etree.tostring(doc, encoding="unicode")
        return result

    def name_get(self):
        res = super(G2PProgramMembership, self).name_get()
        for rec in self:
            name = ""
            if rec.program_id:
                name += "[" + rec.program_id.name + "] "
            if rec.partner_id:
                name += rec.partner_id.name
            res.append((rec.id, name))
        return res

    def open_beneficiaries_form(self):
        for rec in self:
            return {
                "name": "Program Beneficiaries",
                "view_mode": "form",
                "res_model": "g2p.program_membership",
                "res_id": rec.id,
                "view_id": self.env.ref("g2p_programs.view_program_membership_form").id,
                "type": "ir.actions.act_window",
                "target": "new",
                "context": {
                    "target_type": rec.program_id.target_type,
                    "default_program_id": rec.program_id.id,
                },
            }

    def open_registrant_form(self):
        if self.partner_id.is_group:
            return {
                "name": "Group Member",
                "view_mode": "form",
                "res_model": "res.partner",
                "res_id": self.partner_id.id,
                "view_id": self.env.ref("g2p_registry_group.view_groups_form").id,
                "type": "ir.actions.act_window",
                "target": "new",
                "context": {"default_is_group": True},
                "flags": {"mode": "readonly"},
            }
        else:
            return {
                "name": "Individual Member",
                "view_mode": "form",
                "res_model": "res.partner",
                "res_id": self.partner_id.id,
                "view_id": self.env.ref(
                    "g2p_registry_individual.view_individuals_form"
                ).id,
                "type": "ir.actions.act_window",
                "target": "new",
                "context": {"default_is_group": False},
                "flags": {"mode": "readonly"},
            }

    @api.depends("partner_id")
    def _compute_application_id(self):
        for rec in self:
            d = datetime.today().strftime("%d")
            m = datetime.today().strftime("%m")
            y = datetime.today().strftime("%y")

            random_number = str(random.randint(1, 100000))

            rec.application_id = d + m + y + random_number.zfill(5)

    def verify_eligibility(self):
        eligibility_managers = self.program_id.get_managers(
            constants.MANAGER_ELIGIBILITY
        )
        for em in eligibility_managers:
            em.verify_cycle_eligibility(None, self)
        return
