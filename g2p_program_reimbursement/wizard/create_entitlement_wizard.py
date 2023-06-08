# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class G2PEntitlementWizard(models.TransientModel):
    _inherit = "g2p.entitlement.create.wizard"

    service_provider_id = fields.Many2one("res.partner")

    def generate_create_entitlement_dict(self):
        res = super(G2PEntitlementWizard, self).generate_create_entitlement_dict()
        res["service_provider_id"] = self.service_provider_id.id
        return res
