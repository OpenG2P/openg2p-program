# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

from odoo.addons.g2p_json_field.models import json_field


class G2PProgramRegistrantInfo(models.Model):
    _name = "g2p.program.registrant_info"
    _description = "Program Registrant Info"
    _order = "id desc"

    registrant_id = fields.Many2one(
        "res.partner",
        help="A beneficiary",
        required=False,
        auto_join=True,
        # ondelete='set null'
    )
    program_id = fields.Many2one(
        "g2p.program",
        help="A program",
        required=False,
        auto_join=True,
        # ondelete='set null'
    )

    program_registrant_info = json_field.JSONField("Program Information", default={})

    def open_registrant_form(self):
        return {
            "name": "Program Registrant Info",
            "view_mode": "form",
            "res_model": "g2p.program.registrant_info",
            "res_id": self.id,
            "view_id": self.env.ref(
                "g2p_program_registrant_info.view_program_registrant_info_form"
            ).id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_is_group": True},
            "flags": {"mode": "readonly"},
        }
