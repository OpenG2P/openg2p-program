import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class G2PProgramInherit(models.Model):
    _inherit = "g2p.program"

    def create_new_cycle(self):
        if self.beneficiaries_count <= 0:
            raise UserError(
                _("No enrolled registrants. Enroll registrants to program to create a new cycle.")
            )

        for rec in self:
            message = None
            kind = "success"
            cycle_manager = rec.get_manager(self.MANAGER_CYCLE)
            program_manager = rec.get_manager(self.MANAGER_PROGRAM)

            if not cycle_manager:
                raise UserError(_("No Cycle Manager defined."))
            if not program_manager:
                raise UserError(_("No Program Manager defined."))

            _logger.debug("-" * 80)
            _logger.debug("pm: %s", program_manager)

            new_cycle = program_manager.new_cycle()
            message = _("New cycle %s created.", new_cycle.name)

            if new_cycle.is_not_disbursement:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Cycle"),
                        "message": message,
                        "sticky": False,
                        "type": kind,
                        "next": {
                            "type": "ir.actions.act_window_close",
                        },
                    },
                }
            else:
                wizard = self.env["cycle.creation.wizard"].create(
                    {
                        "cycle_id": new_cycle.id,
                        "name": new_cycle.name,
                        "program_id": new_cycle.program_id.id,
                        "eligibility_domain": new_cycle.eligibility_domain,
                        "inclusion_limit": new_cycle.inclusion_limit,
                    }
                )

                for criterion in new_cycle.sorting_criteria_ids:
                    self.env["cycle.creation.wizard.criteria"].create(
                        {
                            "wizard_id": wizard.id,
                            "field_name": criterion.field_name.id,
                            "order": criterion.order,
                            "sequence": criterion.sequence,
                        }
                    )
                return {
                    "name": _("Update Priority Configuration"),
                    "type": "ir.actions.act_window",
                    "res_model": "cycle.creation.wizard",
                    "view_mode": "form",
                    "res_id": wizard.id,
                    "target": "new",
                }
