from odoo import fields, models


class G2PProgramRegistrant(models.Model):
    _inherit = "g2p.program"

    program_registrant_info_ids = fields.One2many(
        "g2p.program.registrant_info", "program_id", "Program regitrant info"
    )
