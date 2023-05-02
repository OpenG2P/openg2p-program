from odoo import fields, models

from odoo.addons.g2p_programs.models import constants


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

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

    def verify_eligibility(self):
        eligibility_managers = self.program_id.get_managers(
            constants.MANAGER_ELIGIBILITY
        )
        for em in eligibility_managers:
            em.verify_cycle_eligibility(None, self)
        return

    def create_entitlement(self):
        return {
            "name": "Create Entitlement",
            "view_mode": "form",
            "res_model": "g2p.entitlement.wizard",
            "res_id": self.id,
            "view_id": self.env.ref(
                "g2p_program_approval.create_entitlement_wizard_form_view"
            ).id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
