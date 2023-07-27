# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    pmt_config = fields.Boolean(string="Enable PMT", default=False)
    proxy_means_params_ids = fields.One2many(
        "g2p.proxy_means_test_params", "program_id", string="PMT Parameters"
    )


class ProxyMeanTestParams(models.Model):

    _name = "g2p.proxy_means_test_params"
    _description = "Proxy Means Test Params"

    program_id = fields.Many2one("g2p.program")
    pmt_field = fields.Selection(selection="get_fields_label", string="Field")
    pmt_weightage = fields.Float(string="Weightage")

    def get_fields_label(self):
        data = self.env["g2p.program.registrant_info"]

        ir_model_obj = self.env["ir.model.fields"]

        choice = []
        for field in data.fields_get_keys():
            ir_model_field = ir_model_obj.search(
                [("model", "=", "g2p.program.registrant_info"), ("name", "=", field)]
            )
            field_type = ir_model_field.ttype
            if field_type == "integer" and field not in ("pmt_score", "id"):
                choice.append((field, field))
        return choice


class G2PProgramRegistrantInfo(models.Model):
    _inherit = "g2p.program.registrant_info"

    pmt_score = fields.Integer("PMT Score", compute="_compute_pmt_score", store=True)
    program_pmt_config = fields.Boolean(related="program_id.pmt_config", readonly=True)

    @api.constrains("program_registrant_info")
    def _compute_pmt_score(self):

        for rec in self:
            score = 0
            data = rec.env["g2p.proxy_means_test_params"].search(
                [("program_id", "=", rec.program_id.id)]
            )

            for data_row in data:
                score += data_row.pmt_weightage * rec.__getattribute__(
                    data_row.pmt_field
                )

            rec.pmt_score = score
