# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class G2PProgramRegistrantInfo(models.Model):
    _inherit = "g2p.program.registrant_info"

    pmt_score = fields.Float(
        "PMT Score", compute="_compute_pmt_score", digits=(0, 7), store=True
    )
    program_pmt_config = fields.Boolean(related="program_id.pmt_config", readonly=True)

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

    def delete_related_proxy_means_params(self, field):
        proxy_params_to_delete = self.env["g2p.proxy_means_test_params"].search(
            [("pmt_field", "=", field)]
        )
        for param in proxy_params_to_delete:
            param.unlink()
