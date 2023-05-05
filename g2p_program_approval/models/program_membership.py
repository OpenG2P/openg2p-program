from odoo import _, fields, models

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
    payment_ids = fields.One2many(related="partner_id.entitlement_ids.payment_ids")

    def verify_eligibility(self):
        eligibility_managers = self.program_id.get_managers(
            constants.MANAGER_ELIGIBILITY
        )
        member = self
        for em in eligibility_managers:
            member = em.enroll_eligible_registrants(member)
        if len(member) == 0:
            self.state = "not_eligible"
        return

    def enroll_eligible_registrants(self):
        eligibility_managers = self.program_id.get_managers(
            constants.MANAGER_ELIGIBILITY
        )
        member = self
        for em in eligibility_managers:
            member = em.enroll_eligible_registrants(member)
        if len(member) > 0:
            if self.state != "enrolled":
                self.write(
                    {
                        "state": "enrolled",
                        "enrollment_date": fields.Datetime.now(),
                    }
                )

        else:
            self.state = "not_eligible"

        return

    def deduplicate_beneficiaries(self):
        deduplication_managers = self.program_id.get_managers(
            constants.MANAGER_DEDUPLICATION
        )

        message = None
        kind = "success"
        if len(deduplication_managers):
            states = ["draft", "enrolled", "eligible", "paused", "duplicated"]
            duplicates = 0
            for el in deduplication_managers:
                duplicates += el.deduplicate_beneficiaries(states)

                if duplicates > 0:
                    message = _("%s Beneficiaries duplicate.", duplicates)
                    kind = "warning"
        else:
            message = _("No Deduplication Manager defined.")
            kind = "danger"

        if message:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Deduplication"),
                    "message": message,
                    "sticky": True,
                    "type": kind,
                    "next": {
                        "type": "ir.actions.act_window_close",
                    },
                },
            }

    def Back_to_draft(self):
        self.write(
            {
                "state": "draft",
            }
        )
        return

    def Create_entitlement(self):
        return
