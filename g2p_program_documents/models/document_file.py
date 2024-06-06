from odoo import fields, models


class G2PDocument(models.Model):
    _inherit = "storage.file"

    program_membership_id = fields.Many2one("g2p.program_membership")

    entitlement_id = fields.Many2one("g2p.entitlement")

    def get_record(self):
        for record in self:
            return {
                "mimetype": record.mimetype,
                "name": record.name,
                "url": record.url if record.url else "#",
            }
