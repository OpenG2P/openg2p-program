from odoo import models


class G2PDocumentStore(models.Model):
    _inherit = "storage.backend"

    def add_file(self, data, name=None, extension=None, program_membership=None):
        res = super(G2PDocumentStore, self).add_file(
            data, name=name, extension=extension
        )
        if program_membership:
            res.program_membership_id = program_membership
        return res
