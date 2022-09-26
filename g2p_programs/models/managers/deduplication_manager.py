# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import date

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DeduplicationManager(models.Model):
    _name = "g2p.deduplication.manager"
    _description = "Deduplication Manager"
    _inherit = "g2p.manager.mixin"

    program_id = fields.Many2one("g2p.program", "Program")

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_managers = [
            ("g2p.deduplication.manager.default", "Default Deduplication"),
            ("g2p.deduplication.manager.phone_number", "Phone Number Deduplication"),
            ("g2p.deduplication.manager.id_dedup", "ID Deduplication"),
        ]
        for new_manager in new_managers:
            if new_manager not in selection:
                selection.append(new_manager)
        return selection


class BaseDeduplication(models.AbstractModel):
    _name = "g2p.base.deduplication.manager"
    _description = "Base Deduplication Manager"

    # Kind of deduplication possible
    _capability_individual = False
    _capability_group = False

    name = fields.Char("Manager Name", required=True)
    program_id = fields.Many2one("g2p.program", string="Program", required=True)

    def deduplicate_beneficiaries(self, states):
        raise NotImplementedError()

    def _record_duplicate(
        self, manager, beneficiary_ids, reason, comment, check_comment=False
    ):
        """
        This method is used to record a duplicate beneficiary.
        :param beneficiary: The beneficiary.
        :param reason: The reason.
        :param comment: The comment.
        :return:
        """

        # TODO: check this group does not exist already with the same manager and the same beneficiaries or
        #  a subset of them.
        #  1. If the state has been changed to no_duplicate, then we should not record it as duplicate unless there are
        #  additional beneficiaries in the group.
        #  2. Otherwise we update the record.

        # _logger.info("Record duplicate: %s", beneficiary_ids)
        data = {
            "program_id": manager.program_id.id,
            "beneficiary_ids": [(6, 0, beneficiary_ids)],
            "state": "duplicate",
            "reason": reason,
            "comment": comment,
            "deduplication_manager_id": manager,
        }
        # Check if there are changes in beneficiary_ids.
        # If there are, update the g2p.program.membership.duplicate record,
        # otherwise, create a new record.
        if not check_comment:
            domain = [("program_id", "=", manager.program_id.id)]
        else:
            domain = [
                ("program_id", "=", manager.program_id.id),
                ("comment", "=", comment),
            ]
        dup_rec = self.env["g2p.program.membership.duplicate"].search(domain)
        create_rec = True
        if dup_rec:
            for rec in dup_rec:
                res = list(
                    map(
                        lambda r: 1 if r in beneficiary_ids else 0,
                        rec.beneficiary_ids.ids,
                    )
                )
                _logger.info("DEBUG! res: %s", res)

                if 1 in res:
                    _logger.info("DEBUG! Update the duplicate record: %s", data)
                    rec.update(data)
                    create_rec = False
                    break
        if create_rec:
            _logger.info("DEBUG!Create a new duplicate record: %s", data)
            self.env["g2p.program.membership.duplicate"].create(data)


class DefaultDeduplication(models.Model):
    _name = "g2p.deduplication.manager.default"
    _inherit = ["g2p.base.deduplication.manager", "g2p.manager.source.mixin"]
    _description = "Default Deduplication Manager"

    _capability_individual = True
    _capability_group = True

    def deduplicate_beneficiaries(self, states):
        self.ensure_one()
        program = self.program_id
        sql = """
            SELECT * FROM
            (SELECT res_partner.id as partner_id,
                res_partner.name as partner_name,
                g2p_group_membership.group as identity_group_id,
                group_program_membership.id as group_program_membership_id,
                count(*)
            OVER
                (PARTITION BY
                    res_partner.id
                ) AS count
            FROM res_partner
            -- Join to the group it belong to through the individual
            LEFT join g2p_group_membership ON g2p_group_membership.individual = res_partner.id
            -- Join the group to the program
            LEFT join g2p_program_membership as group_program_membership
                ON group_program_membership.partner_id = g2p_group_membership.group
            where
            (
                group_program_membership.program_id = %s
            ) AND (
                group_program_membership.state IN %s
            ) AND (
                res_partner.active = True AND
                res_partner.disabled IS NULL AND
                res_partner.is_registrant = True
            )
            ) tableWithCount
            WHERE tableWithCount.count > 1;"""

        states = (*states,)
        self.env.cr.execute(sql, (program.id, states))
        duplicates = self.env.cr.dictfetchall()
        duplicate_partner_ids = []
        duplicate_beneficiary_ids = []
        duplicate_beneficiary_recs = {}
        for rec in duplicates:
            # _logger.info("DEBUG: queried rec: %s", rec)
            if program.target_type == "group":
                duplicate_partner_ids.append(rec["identity_group_id"])
                duplicate_beneficiary_id = rec["group_program_membership_id"]

                duplicate_beneficiary_ids.append(duplicate_beneficiary_id)
                # Separate duplicates by "partner_id"
                dup_val = rec["partner_id"]
                if not duplicate_beneficiary_recs.get(dup_val):
                    duplicate_beneficiary_recs.update(
                        {
                            dup_val: {
                                "rec_ids": [duplicate_beneficiary_id],
                                "partner_id": rec["partner_id"],
                                "name": rec["partner_name"],
                            }
                        }
                    )
                else:
                    duplicate_beneficiary_recs[dup_val]["rec_ids"].append(
                        duplicate_beneficiary_id
                    )

        # _logger.info(
        #    "DEBUG: duplicate_beneficiary_recs: %s", duplicate_beneficiary_recs
        # )
        if duplicate_beneficiary_ids:
            duplicate_beneficiary_ids = list(set(duplicate_beneficiary_ids))
            for dup in duplicate_beneficiary_recs:
                self._record_duplicate(
                    self,
                    duplicate_beneficiary_recs[dup]["rec_ids"],
                    "Duplicate individuals",
                    "Registrant: %s" % duplicate_beneficiary_recs[dup]["name"],
                    check_comment=True,
                )

            duplicate_beneficiaries = self.env["g2p.program_membership"].browse(
                duplicate_beneficiary_ids
            )
            duplicated_enrolled = duplicate_beneficiaries.filtered(
                lambda rec: rec.state in ("enrolled", "duplicated")
            )
            if len(duplicated_enrolled) == 1:
                # If there is only 1 enrolled that is duplicated, the enrolled one should not be marked as duplicate.
                # otherwise if there is more than 1, then there is a problem!
                # TODO: check how to handle this
                duplicated_enrolled.write({"state": "enrolled"})
                duplicate_beneficiaries = duplicate_beneficiaries.filtered(
                    lambda rec: rec.state != "enrolled"
                )
            duplicate_beneficiaries.filtered(
                lambda rec: rec.state not in ["exited", "not_eligible", "duplicated"]
            ).write({"state": "duplicated"})

            return len(duplicate_beneficiaries)
        else:
            return 0


class IDDocumentDeduplication(models.Model):
    _name = "g2p.deduplication.manager.id_dedup"
    _inherit = ["g2p.base.deduplication.manager", "g2p.manager.source.mixin"]
    _description = "ID Deduplication Manager"

    supported_id_document_types = fields.Many2many(
        "g2p.id.type", string="Supported ID Document Types"
    )

    def deduplicate_beneficiaries(self, states):
        self.ensure_one()
        program = self.program_id
        sql = """
            SELECT * FROM
            (SELECT g2p_reg_id.id as identity_id,
                id_type,
                value,
                g2p_reg_id.partner_id as identity_partner_id,
                g2p_group_membership.group as identity_group_id,
                program_membership.id as program_membership_id,
                group_program_membership.id as group_program_membership_id,
                count(*)
            OVER
                (PARTITION BY
                    id_type,
                    value
                ) AS count
            FROM g2p_reg_id
            -- Join to the group it belong to through the individual
            LEFT join g2p_group_membership ON g2p_group_membership.individual = g2p_reg_id.partner_id
            -- Join the group to the program
            LEFT join g2p_program_membership as group_program_membership
                ON group_program_membership.partner_id = g2p_group_membership.group
            -- Join the registrant to the program
            LEFT join g2p_program_membership as program_membership
                ON program_membership.partner_id = g2p_reg_id.partner_id
            where
            (
                group_program_membership.program_id = %s OR
                program_membership.program_id = %s
            ) AND (
                group_program_membership.state IN %s OR
                program_membership.state IN %s
            ) AND (
                g2p_reg_id.expiry_date IS NULL OR
                g2p_reg_id.expiry_date > CURRENT_DATE
            )
            ) tableWithCount
            WHERE tableWithCount.count > 1;"""

        states = (*states,)
        self.env.cr.execute(sql, (program.id, program.id, states, states))
        duplicates = self.env.cr.dictfetchall()
        duplicate_partner_ids = []
        duplicate_beneficiary_ids = []
        duplicate_beneficiary_recs = {}
        for rec in duplicates:
            # _logger.info("DEBUG: queried rec: %s", rec)
            if program.target_type == "group":
                if rec["identity_group_id"]:
                    duplicate_partner_ids.append(rec["identity_group_id"])
                else:
                    duplicate_partner_ids.append(rec["identity_partner_id"])
                if rec["group_program_membership_id"]:
                    duplicate_beneficiary_id = rec["group_program_membership_id"]
                else:
                    duplicate_beneficiary_id = rec["program_membership_id"]
            else:
                duplicate_partner_ids.append(rec["identity_partner_id"])
                duplicate_beneficiary_id = rec["program_membership_id"]

            duplicate_beneficiary_ids.append(duplicate_beneficiary_id)
            # Separate duplicates by "id_type - value"
            dup_val = str(rec["id_type"]) + "-" + str(rec["value"])
            id_type_name = self.env["g2p.id.type"].browse([rec["id_type"]])[0].name
            if not duplicate_beneficiary_recs.get(dup_val):
                duplicate_beneficiary_recs.update(
                    {
                        dup_val: {
                            "rec_ids": [duplicate_beneficiary_id],
                            "id_type_name": id_type_name,
                            "value": rec["value"],
                        }
                    }
                )
            else:
                duplicate_beneficiary_recs[dup_val]["rec_ids"].append(
                    duplicate_beneficiary_id
                )

        # _logger.info("DEBUG: duplicate partner ids: %s", duplicate_partner_ids)
        for dup in duplicate_beneficiary_recs:
            self._record_duplicate(
                self,
                duplicate_beneficiary_recs[dup]["rec_ids"],
                "Duplicate ID Documents",
                "ID Type: %s, Value: %s"
                % (
                    duplicate_beneficiary_recs[dup]["id_type_name"],
                    duplicate_beneficiary_recs[dup]["value"],
                ),
            )

        duplicate_beneficiaries = self.env["g2p.program_membership"].browse(
            duplicate_beneficiary_ids
        )
        duplicated_enrolled = duplicate_beneficiaries.filtered(
            lambda rec: rec.state in ("enrolled", "duplicated")
        )
        if len(duplicated_enrolled) == 1:
            # If there is only 1 enrolled that is duplicated, the enrolled one should not be marked as duplicate.
            # otherwise if there is more than 1, then there is a problem!
            # TODO: check how to handle this
            duplicated_enrolled.write({"state": "enrolled"})
            duplicate_beneficiaries = duplicate_beneficiaries.filtered(
                lambda rec: rec.state != "enrolled"
            )
        duplicate_beneficiaries.filtered(
            lambda rec: rec.state not in ["exited", "not_eligible", "duplicated"]
        ).write({"state": "duplicated"})

        return len(duplicate_beneficiaries)


class PhoneNumberDeduplication(models.Model):
    """
    When this model is added, it should add also the PhoneNumberDeduplicationEligibilityManager to the eligibility
    criteria.
    """

    _name = "g2p.deduplication.manager.phone_number"
    _inherit = ["g2p.base.deduplication.manager", "g2p.manager.source.mixin"]
    _description = "Phone Number Deduplication Manager"

    # # if set, we verify that the phone number match a given regex
    # phone_regex = fields.Char(string="Phone Regex")

    def deduplicate_beneficiaries(self, states):
        self.ensure_one()
        program = self.program_id
        sql = """
            SELECT * FROM
            (SELECT g2p_phone_number.id as phone_id,
                phone_sanitized,
                g2p_phone_number.partner_id as identity_partner_id,
                g2p_group_membership.group as identity_group_id,
                program_membership.id as program_membership_id,
                group_program_membership.id as group_program_membership_id,
                count(*)
            OVER
                (PARTITION BY
                    phone_sanitized
                ) AS count
            FROM g2p_phone_number
            -- Join to the group it belong to through the individual
            LEFT join g2p_group_membership ON g2p_group_membership.individual = g2p_phone_number.partner_id
            -- Join the group to the program
            LEFT join g2p_program_membership as group_program_membership
                ON group_program_membership.partner_id = g2p_group_membership.group
            -- Join the registrant to the program
            LEFT join g2p_program_membership as program_membership
                ON program_membership.partner_id = g2p_phone_number.partner_id
            where
            (
                group_program_membership.program_id = %s OR
                program_membership.program_id = %s
            ) AND (
                group_program_membership.state IN %s OR
                program_membership.state IN %s
            ) AND (
                g2p_phone_number.disabled IS NULL
            )
            ) tableWithCount
            WHERE tableWithCount.count > 1;"""

        states = (*states,)
        self.env.cr.execute(sql, (program.id, program.id, states, states))
        duplicates = self.env.cr.dictfetchall()
        duplicate_partner_ids = []
        duplicate_beneficiary_ids = []
        duplicate_beneficiary_recs = {}
        for rec in duplicates:
            # _logger.info("DEBUG: queried rec: %s", rec)
            if program.target_type == "group":
                if rec["identity_group_id"]:
                    duplicate_partner_ids.append(rec["identity_group_id"])
                else:
                    duplicate_partner_ids.append(rec["identity_partner_id"])
                if rec["group_program_membership_id"]:
                    duplicate_beneficiary_id = rec["group_program_membership_id"]
                else:
                    duplicate_beneficiary_id = rec["program_membership_id"]
            else:
                duplicate_partner_ids.append(rec["identity_partner_id"])
                duplicate_beneficiary_id = rec["program_membership_id"]

            duplicate_beneficiary_ids.append(duplicate_beneficiary_id)
            # Separate duplicates by "phone_sanitized"
            dup_val = rec["phone_sanitized"]
            if not duplicate_beneficiary_recs.get(dup_val):
                duplicate_beneficiary_recs.update(
                    {
                        dup_val: {
                            "rec_ids": [duplicate_beneficiary_id],
                            "phone_sanitized": dup_val,
                        }
                    }
                )
            else:
                duplicate_beneficiary_recs[dup_val]["rec_ids"].append(
                    duplicate_beneficiary_id
                )
        # _logger.info("DEBUG: duplicate partner ids: %s", duplicate_partner_ids)

        for dup in duplicate_beneficiary_recs:
            self._record_duplicate(
                self,
                duplicate_beneficiary_recs[dup]["rec_ids"],
                "Duplicate Phone Numbers",
                "Phone Number: %s" % duplicate_beneficiary_recs[dup]["phone_sanitized"],
            )

        duplicate_beneficiaries = self.env["g2p.program_membership"].browse(
            duplicate_beneficiary_ids
        )

        duplicated_enrolled = duplicate_beneficiaries.filtered(
            lambda rec: rec.state in ("enrolled", "duplicated")
        )
        if len(duplicated_enrolled) == 1:
            # If there is only 1 enrolled that is duplicated, the enrolled one should not be marked as duplicate.
            # otherwise if there is more than 1, then there is a problem!
            # TODO: check how to handle this
            duplicated_enrolled.write({"state": "enrolled"})
            duplicate_beneficiaries = duplicate_beneficiaries.filtered(
                lambda rec: rec.state != "enrolled"
            )
        duplicate_beneficiaries.filtered(
            lambda rec: rec.state not in ["exited", "not_eligible", "duplicated"]
        ).write({"state": "duplicated"})

        return len(duplicate_beneficiaries)


class IDPhoneEligibilityManager(models.Model):
    """
    Add the ID Document and Phone Number Deduplication in the Eligibility Manager
    """

    _inherit = "g2p.eligibility.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_managers = [
            ("g2p.program_membership.manager.id_dedup", "ID Document Eligibility"),
            ("g2p.program_membership.manager.phone_number", "Phone Number Eligibility"),
        ]
        for new_manager in new_managers:
            if new_manager not in selection:
                selection.append(new_manager)
        return selection


class IDDocumentDeduplicationEligibilityManager(models.Model):
    """
    This model is used to check if a beneficiary has the required documents to be deduplicated.
    It uses the IDDocumentDeduplication configuration to perform the check
    """

    _name = "g2p.program_membership.manager.id_dedup"
    _inherit = ["g2p.program_membership.manager", "g2p.manager.source.mixin"]
    _description = "ID Document Deduplication Eligibility"

    eligibility_domain = fields.Text(string="Domain", default="[]")

    def _prepare_eligible_domain(self, membership):
        ids = membership.mapped("partner_id.id")
        registrant_ids = self.env["res.partner"].search([("id", "in", ids)])
        _logger.info("Checking Registrants: %s", registrant_ids)
        registrant_ids_with_id = []
        for i in registrant_ids:
            if i.reg_ids:
                registrant_ids_with_id += [
                    i.id
                    for x in i.reg_ids
                    if x.expiry_date and x.expiry_date > date.today()
                ]
        registrant_ids_with_id = list(dict.fromkeys(registrant_ids_with_id))
        _logger.info("Eligible registrants with ID: %s", registrant_ids_with_id)
        domain = [("id", "in", registrant_ids_with_id)]
        domain += self._safe_eval(self.eligibility_domain)
        return domain

    def enroll_eligible_registrants(self, program_memberships):
        # TODO: check if the beneficiary still match the criterias
        _logger.info("-" * 100)
        _logger.info("Checking eligibility for %s", program_memberships)
        for rec in self:
            beneficiaries = rec._verify_eligibility(program_memberships)
            return self.env["g2p.program_membership"].search(
                [
                    ("partner_id", "in", beneficiaries),
                    ("program_id", "=", self.program_id.id),
                ]
            )

    def verify_cycle_eligibility(self, cycle, membership):
        for rec in self:
            beneficiaries = rec._verify_eligibility(membership)
            return self.env["g2p.cycle.membership"].search(
                [("partner_id", "in", beneficiaries)]
            )

    def _verify_eligibility(self, membership):
        domain = self._prepare_eligible_domain(membership)
        _logger.info("Eligibility domain: %s", domain)
        beneficiaries = self.env["res.partner"].search(domain).ids
        _logger.info("Beneficiaries: %s", beneficiaries)
        return beneficiaries


class PhoneNumberDeduplicationEligibilityManager(models.Model):
    """
    This model is used to check if a beneficiary has a phone number to be deduplicated
    It uses the PhoneNumberDeduplication configuration to perform the check
    """

    _name = "g2p.program_membership.manager.phone_number"
    _inherit = ["g2p.program_membership.manager", "g2p.manager.source.mixin"]
    _description = "Phone Number Deduplication Eligibility"

    eligibility_domain = fields.Text(string="Domain", default="[]")

    def _prepare_eligible_domain(self, membership):
        ids = membership.mapped("partner_id.id")
        registrant_ids = self.env["res.partner"].search([("id", "in", ids)])
        _logger.info("Checking Registrants: %s", registrant_ids)
        registrant_ids_with_phone = []
        for i in registrant_ids:
            if i.phone_number_ids:
                registrant_ids_with_phone += [
                    i.id for x in i.phone_number_ids if not x.disabled
                ]
        registrant_ids_with_phone = list(dict.fromkeys(registrant_ids_with_phone))
        _logger.info("Eligible registrants with Phone: %s", registrant_ids_with_phone)

        domain = [("id", "in", registrant_ids_with_phone)]
        domain += self._safe_eval(self.eligibility_domain)
        return domain

    def enroll_eligible_registrants(self, program_memberships):
        # TODO: check if the beneficiary still match the criterias
        _logger.info("-" * 100)
        _logger.info("Checking eligibility for %s", program_memberships)
        for rec in self:
            beneficiaries = rec._verify_eligibility(program_memberships)
            return self.env["g2p.program_membership"].search(
                [
                    ("partner_id", "in", beneficiaries),
                    ("program_id", "=", self.program_id.id),
                ]
            )

    def verify_cycle_eligibility(self, cycle, membership):
        for rec in self:
            beneficiaries = rec._verify_eligibility(membership)
            return self.env["g2p.cycle.membership"].search(
                [("partner_id", "in", beneficiaries)]
            )

    def _verify_eligibility(self, membership):
        domain = self._prepare_eligible_domain(membership)
        _logger.info("Eligibility domain: %s", domain)
        beneficiaries = self.env["res.partner"].search(domain).ids
        _logger.info("Beneficiaries: %s", beneficiaries)
        return beneficiaries
