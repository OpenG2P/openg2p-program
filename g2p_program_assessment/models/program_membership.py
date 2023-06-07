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

    assessment_ids = fields.One2many("g2p.program.assessment", "program_membership_id")

    show_create_entitlement_button = fields.Boolean(
        compute="_compute_show_create_entitlement"
    )

    def _compute_show_create_entitlement(self):
        for rec in self:
            rec.show_create_entitlement_button = self.env[
                "g2p.entitlement.create.wizard"
            ].is_show_create_entitlement(rec)

    def prepare_assessment(self):
        return {
            "name": _("Assessments"),
            "type": "ir.actions.act_window",
            "res_model": "g2p.program_membership.assessment.wizard",
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "context": {
                "create": False,
                "edit": False,
                "default_program_membership_id": self.id,
            },
            "flags": {"mode": "readonly"},
        }

    def open_entitlement_form_wizard(self):
        return self.env["g2p.entitlement.create.wizard"].open_entitlement_form_wizard(
            self
        )
