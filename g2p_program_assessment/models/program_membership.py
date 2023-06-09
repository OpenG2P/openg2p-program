# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


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
    show_reject_application_assessment_button = fields.Boolean(
        compute="_compute_reject_application_assessment"
    )

    def _compute_show_create_entitlement(self):
        for rec in self:
            rec.show_create_entitlement_button = self.env[
                "g2p.entitlement.create.wizard"
            ].is_show_create_entitlement(rec)

    def _compute_reject_application_assessment(self):
        for rec in self:
            rec.show_reject_application_assessment_button = False
            try:
                reg_info = rec.latest_registrant_info
                if (
                    reg_info
                    and reg_info.state in ("active", "inprogress")
                    and rec.assessment_ids.filtered(
                        lambda x: x.create_date > reg_info.create_date
                    )
                ):
                    rec.show_reject_application_assessment_button = True
            except Exception as e:
                _logger.warning(
                    "During compute reject: Program Registrant Info is not installed. %s",
                    e,
                )

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

    def reject_application_assessment(self):
        self.ensure_one()
        try:
            is_found = self.env[
                "g2p.program.registrant_info"
            ].trigger_latest_status_membership(
                self, "rejected", check_states=("active", "inprogress")
            )
            if is_found:
                message = _("Application rejected.")
                kind = "success"
            else:
                message = _("No Application found.")
                kind = "success"
        except Exception as e:
            _logger.warning(
                "During reject: Program Registrant Info is not installed. %s", e
            )
            message = _("Application could not be rejected.")
            kind = "danger"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Reject"),
                "message": message,
                "sticky": True,
                "type": kind,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }
