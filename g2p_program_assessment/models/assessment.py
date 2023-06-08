# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models


class G2PProgramAssessment(models.Model):
    _name = "g2p.program.assessment"
    _description = "G2P Assessment"
    _order = "id asc"

    # TODO: default name can be dynamic from program name + registrant combo
    name = fields.Char(default="Assessment")

    remarks_id = fields.Many2one("mail.message")

    author_id = fields.Many2one(related="remarks_id.author_id")

    assessment_date = fields.Datetime(related="remarks_id.date")

    program_membership_id = fields.Many2one("g2p.program_membership")

    entitlement_id = fields.Many2one("g2p.entitlement")

    @api.model
    def post_assessment(
        self,
        body,
        res_model,
        res_ids,
        subject=None,
        message_type="comment",
        subtype_id=None,
        partner_ids=None,
        add_sign=True,
        record_name="",
    ):
        if not isinstance(res_ids, list):
            res_ids = [
                res_ids,
            ]
        message_dicts = []
        for res_id in res_ids:
            subject = subject or self.compute_subject(res_model, res_id)
            partner_ids = partner_ids or self.compute_partner_ids(res_model, res_id)
            record_name = (
                record_name or (partner_ids and partner_ids[0].name) or subject
            )
            message_dicts.append(
                {
                    "author_id": self.env.user.partner_id.id,
                    "email_from": f'"{self.env.user.name}" <{self.env.user.email}>',
                    "model": res_model,
                    "res_id": res_id,
                    "body": body,
                    "subject": subject,
                    "message_type": message_type,
                    "subtype_id": subtype_id or self.env.ref("mail.mt_note").id,
                    "partner_ids": [partner.id for partner in partner_ids],
                    "add_sign": add_sign,
                    "record_name": record_name,
                }
            )
        messages = self.env["mail.thread"]._message_create(message_dicts)

        assessments = self.create(
            [
                {
                    "name": message.subject,
                    "remarks_id": message.id,
                    self.get_res_field_name(res_model): res_ids[i],
                }
                for i, message in enumerate(messages)
            ]
        )
        for assessment in assessments:
            if assessment.entitlement_id:
                assessment.program_membership_id = assessment.entitlement_id.partner_id.program_membership_ids.filtered(
                    lambda x: x.program_id.id == assessment.entitlement_id.program_id.id
                )
            elif assessment.program_membership_id:
                entitlement = assessment.program_membership_id.partner_id.entitlement_ids.filtered(
                    lambda x: x.program_id.id
                    == assessment.program_membership_id.program_id.id
                ).sorted(
                    "create_date", reverse=True
                )
                if entitlement:
                    entitlement = entitlement[0]
                    if entitlement.state in ("draft",):
                        assessment.entitlement_id = entitlement.id
        return assessments

    @api.model
    def get_res_field_name(self, res_model):
        if res_model == "g2p.program_membership":
            return "program_membership_id"
        elif res_model == "g2p.entitlement":
            return "entitlement_id"
        else:
            return None

    def compute_subject(self, res_model, res_id):
        program_memberships = self.compute_program_memberships(res_model, res_id)
        assess_number = len(program_memberships.assessment_ids) + 1
        program_name = program_memberships.program_id.name
        partner_name = program_memberships.partner_id.name
        res = f"Assessment #{assess_number} for {partner_name} under {program_name} program"
        return _(res)

    def compute_program_memberships(self, res_model, res_id):
        if res_model == "g2p.program_membership":
            return self.env[res_model].browse(res_id)
        elif res_model == "g2p.entitlement":
            entitlement = self.env[res_model].browse(res_id)
            return self.env["g2p.program_membership"].search(
                [
                    ("program_id", "=", entitlement.program_id.id),
                    ("partner_id", "=", entitlement.partner_id.id),
                ]
            )
        else:
            return None

    def compute_partner_ids(self, res_model, res_id):
        if res_model == "g2p.program_membership":
            return self.env[res_model].browse(res_id).partner_id
        elif res_model == "g2p.entitlement":
            return self.env[res_model].browse(res_id).partner_id
        else:
            return None

    @api.model
    def get_rendering_context(self, res_model, res_id):
        return {
            "assessments": [
                {
                    "author_name": assess.author_id.name,
                    "author_id": assess.author_id.id,
                    "assessment_date": assess.assessment_date,
                    "body": assess.remarks_id.body,
                }
                for assess in self.search(
                    [(self.get_res_field_name(res_model), "=", res_id)],
                    order="create_date desc",
                )
            ]
        }
