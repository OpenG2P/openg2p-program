# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class G2PProgramRegistrantInfo(models.Model):
    _inherit = "g2p.program.registrant_info"

    program_pmt_config = fields.Boolean(related="program_id.pmt_config", readonly=True)
    pmt_score = fields.Float("PMT Score", compute="_compute_pmt_score", store=True)
    latest_registrant_info = fields.Many2one(
        "g2p.program.registrant_info", compute="_compute_latest_registrant_info"
    )
    latest_pmt_score = fields.Float(
        related="latest_registrant_info.pmt_score", string="Latest PMT Score", store=True
    )

    @api.depends(
        "program_registrant_info",
        "program_id.proxy_means_params_ids.pmt_field",
        "program_id.proxy_means_params_ids.pmt_weightage",
    )
    def _compute_pmt_score(self):
        for rec in self:
            score = 0.0

            pmt_params = rec.program_id.proxy_means_params_ids

            for param in pmt_params:
                score += param.pmt_weightage * rec.__getattribute__(param.pmt_field)

            rec.pmt_score = score

    def _compute_latest_registrant_info(self):
        for rec in self:
            if rec.program_id and rec.registrant_id:
                reg_info = self.search(
                    [("program_id", "=", rec.program_id.id), ("registrant_id", "=", rec.registrant_id.id)]
                ).sorted("create_date", reverse=True)

                if reg_info:
                    reg_info.update({"latest_pmt_score": rec.pmt_score})
                    rec.latest_registrant_info = reg_info[0]
            else:
                rec.latest_registrant_info = None

    def delete_related_proxy_means_params(self, field):
        proxy_params_to_delete = self.env["g2p.proxy_means_test_params"].search([("pmt_field", "=", field)])
        for param in proxy_params_to_delete:
            param.unlink()
