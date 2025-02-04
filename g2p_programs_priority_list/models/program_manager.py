import logging
from datetime import datetime, timedelta

from odoo import fields, models

from odoo.addons.g2p_programs.models.programs import G2PProgram

_logger = logging.getLogger(__name__)


class DefaultProgramManagerInherited(models.Model):
    _inherit = "g2p.program.manager.default"

    is_disbursement_through_priority_list = fields.Boolean(
        string="Disbursement Through Priority List", default=False
    )

    def new_cycle(self):
        """
        Create the next cycle of the program.
        If `is_disbursement_through_priority_list` is False, it copies enrolled beneficiaries.
        """
        self.ensure_one()

        for rec in self:
            cycles = self.env["g2p.cycle"].search([("program_id", "=", rec.program_id.id)])
            _logger.debug("Cycles found: %s", cycles)

            cm = rec.program_id.get_manager(G2PProgram.MANAGER_CYCLE)

            if not cycles:
                _logger.debug("Creating first cycle with cycle manager: %s", cm)
                new_cycle = cm.new_cycle("Cycle 1", datetime.now(), 1)
            else:
                last_cycle = rec.last_cycle()
                new_sequence = last_cycle.sequence + 1
                start_date = last_cycle.end_date + timedelta(days=1)
                new_cycle = cm.new_cycle(f"Cycle {new_sequence}", start_date, new_sequence)

            # Only copy beneficiaries if disbursement is NOT based on priority list
            if not rec.is_disbursement_through_priority_list:
                if new_cycle:
                    program_beneficiaries = rec.program_id.get_beneficiaries("enrolled").mapped(
                        "partner_id.id"
                    )
                    cm.add_beneficiaries(new_cycle, program_beneficiaries, "enrolled")

            return new_cycle
