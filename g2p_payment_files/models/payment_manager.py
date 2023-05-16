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

    # This is a one2one relation
    crypto_key_set = fields.One2many("g2p.crypto.key.set", "file_payment_manager_id")

    @api.model
    def create(self, values):
        if not values.get("crypto_key_set", None):
            values["crypto_key_set"] = [(0, 0, {})]
        return super(G2PFilesPaymentManager, self).create(values)

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

        if self.create_batch:
            if batches:
                # Render all qrcodes and store for all payment batches
                for batch_tag in self.batch_tag_ids:
                    qrcode_config_ids = None
                    for file_config in batch_tag.file_config_ids:
                        if not qrcode_config_ids:
                            qrcode_config_ids = file_config.qrcode_config_ids
                        else:
                            qrcode_config_ids += file_config.qrcode_config_ids
                    tag_batches = batches.filtered(
                        lambda x: x.tag_id.id == batch_tag.id
                    )

                    if batch_tag.render_files_per_payment:
                        render_res_records = tag_batches.payment_ids
                        render_res_ids = render_res_records.ids
                        render_res_model = "g2p.payment.batch"
                        res_id_field_in_qrcode_model = "payment_batch_id"
                    else:
                        render_res_records = tag_batches
                        render_res_ids = render_res_records.ids
                        render_res_model = "g2p.payment"
                        res_id_field_in_qrcode_model = "payment_id"

                    for qrcode_config in qrcode_config_ids:
                        qrcode_config.render_datas_and_store(
                            render_res_model,
                            render_res_ids,
                            self.crypto_key_set[0],
                            res_id_field_in_qrcode_model,
                        )

                    # Render the voucher template itself
                    for file_config in batch_tag.file_config_ids:
                        files = file_config.render_and_store(
                            render_res_model, render_res_ids, self.file_document_store
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
                        self.crypto_key_set[0],
                        res_id_field_in_qrcode_model="payment_id",
                    )

                # Render the voucher template itself
                for file_config in file_configs:
                    files = file_config.render_and_store(
                        "g2p.payment", payments.ids, self.file_document_store
                    )
                    for i, rec in enumerate(payments):
                        rec.payment_file_ids = [(4, files[i].id)]
        return payments, batches


class G2PPaymentBatchTag(models.Model):
    _inherit = "g2p.payment.batch.tag"

    render_files_per_payment = fields.Boolean(default=False)

    file_config_ids = fields.Many2many("g2p.payment.file.config")
