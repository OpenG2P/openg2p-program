# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    self_service_portal_form = fields.Many2one(
        "website.page",
        string="Program Form",
        domain="[('is_portal_form', '=', 'True')]",
    )

    multiple_form_submission = fields.Boolean(default=False)

    file_size_ssp = fields.Float()

    @api.constrains("self_service_portal_form")
    def update_form_template(self):
        form_view = self.self_service_portal_form.view_id
        if form_view:
            form_view_template = form_view.arch_db
            form_view.write(
                {
                    "arch_db": form_view_template.replace(
                        "website.layout",
                        "g2p_self_service_portal.self_service_form_template",
                    ).replace(
                        "g2p_service_provider_portal.reimbursement_submission_form_template",
                        "g2p_self_service_portal.self_service_form_template",
                    )
                }
            )
