import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class EntitlementRegInfo(models.Model):
    _inherit = "g2p.entitlement"

    # The Mapping between registrant_info and entitlement is only one to one for now.
    program_registrant_info_ids = fields.One2many("g2p.program.registrant_info", "entitlement_id")
    latest_registrant_info = fields.Many2one(
        "g2p.program.registrant_info", compute="_compute_latest_registrant_info"
    )
    latest_registrant_info_status = fields.Selection(related="latest_registrant_info.state")

    def _compute_latest_registrant_info(self):
        for rec in self:
            if rec.program_registrant_info_ids:
                rec.latest_registrant_info = rec.program_registrant_info_ids[0]
            else:
                rec.latest_registrant_info = None
