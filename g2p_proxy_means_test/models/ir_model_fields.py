# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    def unlink(self):
        for rec in self:
            delete_field = rec.name
            reg_info = rec.env["g2p.program.registrant_info"]
            reg_info.delete_related_proxy_means_params(delete_field)

        return super().unlink()
