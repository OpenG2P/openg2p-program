from odoo import api, fields, models


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    supporting_document_ids = fields.One2many("storage.file", "entitlement_id")

    def copy_documents_from_beneficiary(self):
        for rec in self:
            prog_mem = rec.partner_id.program_membership_ids.filtered(
                lambda x: x.program_id.id == rec.program_id.id
            )[0]
            old_entitlements = rec.partner_id.entitlement_ids.filtered(
                lambda x: x.program_id.id == rec.program_id.id and x.id != rec.id
            )
            old_entitlements = old_entitlements.sorted("create_date", reverse=True)
            old_entitlement = None
            if old_entitlements:
                old_entitlement = old_entitlements[0]
            for document in prog_mem.supporting_documents_ids:
                if not document.entitlement_id:
                    if (not old_entitlement) or (
                        document.create_date > old_entitlement.create_date
                    ):
                        document.entitlement_id = rec

    @api.constrains("supporting_document_ids")
    def _constrains_supporting_document_ids(self):
        for rec in self:
            for document in rec.supporting_document_ids:
                if not document.program_membership_id:
                    prog_mem = rec.partner_id.program_membership_ids.filtered(
                        lambda x: x.program_id.id == rec.program_id.id
                    )
                    if prog_mem:
                        document.program_membership_id = prog_mem[0]
