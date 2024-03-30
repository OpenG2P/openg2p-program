# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class G2PCreateProgramWizard(models.TransientModel):
    _inherit = "g2p.program.create.wizard"

    pmt_config = fields.Boolean(string="Enable PMT", default=False)
    proxy_means_params_ids = fields.One2many(
        "g2p.proxy_means_test_params_wizard", "program_id", string="PMT Parameters"
    )

    def create_program(self):
        res = super().create_program()

        program = self.env["g2p.program"].browse(res["res_id"])

        if self.pmt_config:
            data = self.proxy_means_params_ids

            for rec in data:
                self.env["g2p.proxy_means_test_params"].create(
                    {
                        "program_id": program.id,
                        "pmt_field": rec.pmt_field,
                        "pmt_weightage": rec.pmt_weightage,
                    }
                )

            program.update(
                {
                    "pmt_config": self.pmt_config,
                    "proxy_means_params_ids": self.env["g2p.proxy_means_test_params"].search(
                        [("program_id", "=", program.id)]
                    ),
                }
            )

        return res


class ProxyMeanTestParamsWizard(models.TransientModel):
    _name = "g2p.proxy_means_test_params_wizard"
    _description = "Proxy Means Test Params Wizard"

    program_id = fields.Many2one("g2p.program.create.wizard")
    pmt_field = fields.Selection(selection="get_fields_label", string="Field")
    pmt_weightage = fields.Float(string="Weightage")

    def get_fields_label(self):
        data = self.env["g2p.program.registrant_info"]

        ir_model_obj = self.env["ir.model.fields"]

        choice = []
        for field in data._fields.items():
            ir_model_field = ir_model_obj.search(
                [("model", "=", "g2p.program.registrant_info"), ("name", "=", field)]
            )
            field_type = ir_model_field.ttype
            if field_type in ["integer", "float"] and field not in ("pmt_score", "id"):
                choice.append((field, field))
        return choice
