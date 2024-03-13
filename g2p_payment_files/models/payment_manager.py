# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.file",
            "File Payment Manager",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PFilesPaymentManager(models.Model):
    _name = "g2p.program.payment.manager.file"
    _inherit = "g2p.program.payment.manager.default"
    _description = "File based Payment Manager"

    file_document_store = fields.Many2one("storage.backend")

    payment_file_config_ids = fields.Many2many("g2p.payment.file.config")

    encryption_provider_id = fields.Many2one("g2p.encryption.provider")

    batch_tag_ids = fields.Many2many(
        "g2p.payment.batch.tag",
        "g2p_pay_batch_tag_pay_manager_files",
        string="Batch Tags",
        ondelete="cascade",
    )

    def _prepare_payments(self, cycle, entitlements):
        payments, batches = super(G2PFilesPaymentManager, self)._prepare_payments(
            cycle, entitlements
        )

        file_document_store = self.file_document_store
        if not file_document_store:
            file_document_store = self.program_id.supporting_documents_store
        if self.create_batch:
            if batches:
                # Render all qrcodes and store for all payment batches
                for batch_tag in self.batch_tag_ids:
                    qrcode_config_ids = []
                    for file_config in batch_tag.file_config_ids:
                        if not qrcode_config_ids:
                            qrcode_config_ids = file_config.qrcode_config_ids
                        else:
                            qrcode_config_ids += file_config.qrcode_config_ids
                    tag_batches = batches.filtered(
                        lambda x: x.tag_id.id == batch_tag.id
                    )

                    if not batch_tag.render_files_per_payment:
                        render_res_records = tag_batches
                        render_res_ids = render_res_records.ids
                        render_res_model = "g2p.payment.batch"
                        res_id_field_in_qrcode_model = "payment_batch_id"
                    else:
                        render_res_records = tag_batches.payment_ids
                        render_res_ids = render_res_records.ids
                        render_res_model = "g2p.payment"
                        res_id_field_in_qrcode_model = "payment_id"

                    for qrcode_config in qrcode_config_ids:
                        qrcode_config.render_datas_and_store(
                            render_res_model,
                            render_res_ids,
                            self.get_encryption_provider(),
                            res_id_field_in_qrcode_model,
                        )

                    # Render the voucher template itself
                    for file_config in batch_tag.file_config_ids:
                        files = file_config.render_and_store(
                            render_res_model, render_res_ids, file_document_store
                        )

                        for i, rec in enumerate(render_res_records):
                            rec.payment_file_ids = [(4, files[i].id)]

        else:
            if payments:
                file_configs = self.payment_file_config_ids
                qrcode_config_ids = (
                    file_configs.qrcode_config_ids if file_configs else []
                )
                for qrcode_config in qrcode_config_ids:
                    qrcode_config.render_datas_and_store(
                        "g2p.payment",
                        payments.ids,
                        self.get_encryption_provider(),
                        res_id_field_in_qrcode_model="payment_id",
                    )

                # Render the voucher template itself
                for file_config in file_configs:
                    files = file_config.render_and_store(
                        "g2p.payment", payments.ids, file_document_store
                    )
                    for i, rec in enumerate(payments):
                        rec.payment_file_ids = [(4, files[i].id)]
        return payments, batches

    def _send_payments(self, batches):
        raise NotImplementedError()

    def get_encryption_provider(self):
        self.ensure_one()
        prov = self.encryption_provider_id
        if not prov:
            prov = self.env.ref("g2p_encryption.encryption_provider_default")
        return prov


class G2PPaymentBatchTag(models.Model):
    _inherit = "g2p.payment.batch.tag"

    render_files_per_payment = fields.Boolean(
        default=False, string="Render per payment instead of batch"
    )

    file_config_ids = fields.Many2many("g2p.payment.file.config")
