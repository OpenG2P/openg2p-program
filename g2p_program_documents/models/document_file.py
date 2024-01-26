from odoo import fields, models


class G2PDocument(models.Model):
    _inherit = "storage.file"

    program_membership_id = fields.Many2one("g2p.program_membership")

    entitlement_id = fields.Many2one("g2p.entitlement")

    attachment_id = fields.Many2one("ir.attachment", string="Attachment")

    def get_binary(self):
        for record in self:
            if not record.attachment_id:
                data = record.data
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": "Preview File",
                        "datas": data,
                        "res_model": self._name,
                        "res_id": record.id,
                        "type": "binary",
                    }
                )
                record.attachment_id = attachment.id

            return {
                "id": record.attachment_id.id,
                "mimetype": record.attachment_id.mimetype,
                "index_content": record.attachment_id.index_content,
                "url": record.url if record.url else "#",
            }
