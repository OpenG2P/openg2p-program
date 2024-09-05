from odoo import fields, models


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    self_service_portal_form = fields.Many2one("formio.builder", string="Program Form")

    is_multiple_form_submission = fields.Boolean(default=False)
