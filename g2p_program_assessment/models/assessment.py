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

    res_ref = fields.Reference(
        string="Resource Reference", selection="_selection_assessment_res_model"
    )

    @api.model
    def _selection_assessment_res_model(self):
        return [
            ("g2p.program_membership", "G2P Program Membership"),
            # TODO: To be Impl:
            # ("g2p.entitlement","G2P Program Membership"),
        ]

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
        return self.create(
            [
                {
                    "name": message.subject,
                    "remarks_id": message.id,
                    "res_ref": f"{res_model},{res_ids[i]}",
                }
                for i, message in enumerate(messages)
            ]
        )

    def compute_subject(self, res_model, res_id):
        if res_model == "g2p.program_membership":
            program_memberships = self.env[res_model].browse(res_id)
            assess_number = len(program_memberships.assessment_ids)
            program_name = program_memberships.program_id.name
            partner_name = program_memberships.partner_id.name
            res = f"Assessment #{assess_number} for {partner_name} under {program_name} program"
            return _(res)
        return None

    def compute_partner_ids(self, res_model, res_id):
        if res_model == "g2p.program_membership":
            return self.env[res_model].browse(res_id).partner_id
        else:
            return None

    @api.model
    def object_to_ref(self, record):
        record.ensure_one()
        manager_ref_id = str(record)
        s = manager_ref_id.find("(")
        res_model = manager_ref_id[:s]
        res_id = record.id
        return f"{res_model},{res_id}"

    @api.model
    def get_rendering_context(self, res_ref):
        return {
            "assessments": [
                {
                    "author_name": assess.author_id.name,
                    "author_id": assess.author_id.id,
                    "assessment_date": assess.assessment_date,
                    "body": assess.remarks_id.body,
                }
                for assess in self.search(
                    [("res_ref", "=", res_ref)], order="create_date desc"
                )
            ]
        }
