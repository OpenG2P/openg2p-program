import base64

import magic

from odoo import fields, models


class G2PDocument(models.Model):
    _inherit = "storage.file"

    program_membership_id = fields.Many2one("g2p.program_membership")

    entitlement_id = fields.Many2one("g2p.entitlement")

    def get_record(self):
        for record in self:
            if not record.mimetype:
                binary_data = base64.b64decode(record.data)
                mime = magic.Magic(mime=True)
                mimetype = mime.from_buffer(binary_data)
                return {
                    "mimetype": mimetype,
                    "name": record.name,
                    "url": record.url if record.url else "#",
                }

            else:
                return {
                    "mimetype": record.mimetype,
                    "name": record.name,
                    "url": record.url if record.url else "#",
                }
