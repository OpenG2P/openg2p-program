# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import _, fields, models


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    assessment_status = fields.Selection(
        [
            ("draft", "In Progress"),
            ("done", "Done"),
            ("closed", "Closed"),
        ]
    )

    assessment_ids = fields.Many2many(
        "g2p.program.assessment", compute="_compute_assessment_ids"
    )

    def _compute_assessment_ids(self):
        for rec in self:
            rec_ref = self.env["g2p.program.assessment"].object_to_ref(self)
            assessments = self.env["g2p.program.assessment"].search(
                [("res_ref", "=", rec_ref)]
            )
            rec.assessment_ids = [(4, assess.id) for assess in assessments]

    def prepare_assessment(self):
        wizard = self.env["g2p.program_membership.assessment.wizard"].create(
            {
                "program_membership_id": self.id,
            }
        )
        return {
            "name": _("Assessments"),
            "type": "ir.actions.act_window",
            "res_id": wizard.id,
            "res_model": "g2p.program_membership.assessment.wizard",
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "context": {"create": False, "edit": False},
            "flags": {"mode": "readonly"},
        }
