# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    pmt_config = fields.Boolean(string="Enable PMT", default=False)
    proxy_means_params_ids = fields.One2many(
        "g2p.proxy_means_test_params", "program_id", string="PMT Parameters"
    )
