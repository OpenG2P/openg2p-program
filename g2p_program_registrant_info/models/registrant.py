from odoo import fields, models


class G2PRegistrant(models.Model):
    _inherit = "res.partner"

    # additional_g2p_info = json_field.JSONField("Additional Information", default={})

    program_registrant_info_ids = fields.One2many(
        "g2p.program.registrant_info", "registrant_id", "Program Registrant info"
    )
