# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class G2PCreateProgramWizard(models.TransientModel):
    _inherit = "g2p.program.create.wizard"

    self_service_portal_form = fields.Many2one(
        "website.page",
        string="Program Form",
        domain="[('is_portal_form', '=', 'True')]",
    )

    multiple_form_submission = fields.Boolean(default=False)

    def create_program(self):
        res = super().create_program()

        program = self.env["g2p.program"].browse(res["res_id"])
        portal_form = self.self_service_portal_form

        if portal_form:
            program.self_service_portal_form = portal_form

        program.multiple_form_submission = self.multiple_form_submission

        return res
