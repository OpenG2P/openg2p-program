from odoo import fields, models


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    auto_enrol_partners = fields.Boolean()
    auto_enrol_partners_domain = fields.Text()
    auto_enrol_partners_delete_not_eligible = fields.Boolean()
