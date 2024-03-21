# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProxyMeanTestParams(models.Model):

    _name = "g2p.proxy_means_test_params"
    _description = "Proxy Means Test Params"

    program_id = fields.Many2one("g2p.program")
    pmt_field = fields.Selection(selection="get_fields_label", string="Field")
    pmt_weightage = fields.Float(string="Weightage", digits=(0, 4))

    def get_fields_label(self):
        reg_info = self.env["g2p.program.registrant_info"]

        ir_model_obj = self.env["ir.model.fields"]

        choice = []
        for field in reg_info._fields.items():
            ir_model_field = ir_model_obj.search(
                [("model", "=", "g2p.program.registrant_info"), ("name", "=", field[0])]
            )
            field_type = ir_model_field.ttype
            if field_type in ["integer", "float"] and field[0] not in (
                "pmt_score",
                "id",
                "sl_no",
            ):
                choice.append((field[0], field[0]))
        return choice
