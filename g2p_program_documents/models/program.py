from odoo import fields, models


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    supporting_documents_store = fields.Many2one("storage.backend")
