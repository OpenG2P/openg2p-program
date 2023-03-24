from odoo import fields, models
from odoo.addons.g2p_json_field.models import json_field


class G2PProgramRegistrant(models.Model):
    _inherit = "g2p.program"

   

    program_registrant_info_ids = fields.One2many(
        "g2p.program.registrant_info", "program", "Program regitrant info"
    )
