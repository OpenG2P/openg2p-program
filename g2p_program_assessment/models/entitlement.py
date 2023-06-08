import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PAssessmentEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    assessment_ids = fields.One2many("g2p.program.assessment", "entitlement_id")

    def copy_assessments_from_beneficiary(self):
        for rec in self:
            prog_mem = rec.partner_id.program_membership_ids.filtered(
                lambda x: x.program_id.id == rec.program_id.id
            )
            assessments_to_copy = []
            old_entitlement = rec.partner_id.entitlement_ids.filtered(
                lambda x: x.program_id.id == rec.program_id.id and x.id != rec.id
            ).sorted("create_date", reverse=True)
            if old_entitlement:
                old_entitlement = old_entitlement[0]
            for assessment in prog_mem.assessment_ids:
                if assessment.assessment_date < rec.create_date:
                    if (not old_entitlement) or (
                        old_entitlement.create_date < assessment.assessment_date
                    ):
                        assessments_to_copy.append((4, assessment.id))
            if assessments_to_copy:
                rec.assessment_ids = assessments_to_copy


class DefaultEntitlementManagerForAssessment(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def prepare_entitlements(self, cycle, beneficiaries):
        ents = super(DefaultEntitlementManagerForAssessment, self).prepare_entitlements(
            cycle, beneficiaries
        )
        if ents:
            ents.copy_assessments_from_beneficiary()
        return ents
