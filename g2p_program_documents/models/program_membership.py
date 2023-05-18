from odoo import fields, models


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    supporting_documents_ids = fields.One2many("storage.file", "program_membership_id")
