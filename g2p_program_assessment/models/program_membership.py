# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    assessment_ids = fields.One2many("g2p.program.assessment", "program_membership_id")

    show_prepare_assessment_button = fields.Boolean(
        compute="_compute_show_prepare_assessment"
    )
    show_create_entitlement_button = fields.Boolean(
        compute="_compute_show_create_entitlement"
    )
    show_reject_application_assessment_button = fields.Boolean(
        compute="_compute_reject_application_assessment"
    )

    def _compute_show_prepare_assessment(self):
        for rec in self:
            show_prepare = True
            try:
                latest_reg_info = rec.latest_registrant_info
                show_prepare = show_prepare and (
                    # TODO: The following line needs to be discussed.
                    latest_reg_info
                    and latest_reg_info.state not in ("completed", "rejected")
                )
                if (
                    rec.show_reject_application_assessment_button
                    and not rec.show_create_entitlement_button
                ):
                    show_prepare = False
            except Exception as e:
                _logger.warning("Program Registrant info not installed. %s", e)
            rec.show_prepare_assessment_button = show_prepare

    def _compute_show_create_entitlement(self):
        for rec in self:
            # TODO: Consider create wizard with multiple beneficiaries
            latest_entitlements = rec.partner_id.entitlement_ids.filtered(
                lambda x: x.program_id.id == rec.program_id.id
            ).sorted("create_date", reverse=True)
            show_create = rec.state == "enrolled"
            filtered_assessments = rec.assessment_ids.filtered(
                lambda x: (not latest_entitlements)
                or x.create_date > latest_entitlements[0].create_date
            )
            show_create = show_create and (
                (not latest_entitlements) or latest_entitlements[0].state != "draft"
            )

            latest_reg_info = None
            try:
                latest_reg_info = rec.latest_registrant_info
                show_create = show_create and (
                    latest_reg_info and latest_reg_info.state != "rejected"
                )
                filtered_assessments = filtered_assessments.filtered(
                    lambda x: latest_reg_info
                    and (x.create_date > latest_reg_info.create_date)
                )
            except Exception as e:
                _logger.warning("Program Registrant info not installed. %s", e)

            show_create = show_create and len(filtered_assessments) > 0

            rec.show_create_entitlement_button = show_create

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
                self.env[
                    "g2p.program.registrant_info"
                ].reject_entitlement_for_membership(self)
                message = _("Application rejected.")
                kind = "success"
            else:
                message = _("No Application found.")
                kind = "warning"
        except Exception as e:
            _logger.warning(
                "During reject: Program Registrant Info is not installed. %s", e
            )
            message = _("Application was not rejected.")
            kind = "warning"
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
