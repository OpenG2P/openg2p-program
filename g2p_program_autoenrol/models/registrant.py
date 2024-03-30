import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, values):
        registrants = super(G2PRegistrant, self).create(values)
        # The following might not be safe. Re-evaluate.
        try:
            auto_enrol_programs = self.env["g2p.program"].search(
                [
                    ("state", "=", "active"),
                    ("auto_enrol_partners", "=", True),
                ]
            )
            for program in auto_enrol_programs:
                auto_enrol_registrants = registrants.filtered_domain(
                    self.env["base.programs.manager"]._safe_eval(program.auto_enrol_partners_domain)
                )
                if not auto_enrol_registrants:
                    continue
                for registrant in auto_enrol_registrants:
                    member = self.env["g2p.program_membership"].create(
                        {"partner_id": registrant.id, "program_id": program.id}
                    )
                    member.enroll_eligible_registrants()
                    if program.auto_enrol_partners_delete_not_eligible and member.state != "enrolled":
                        member.unlink()
                program._compute_eligible_beneficiary_count()
                program._compute_beneficiary_count()
        except Exception as e:
            _logger.error("Registrant Created. Not auto enrolled into programs", e)
        return registrants
