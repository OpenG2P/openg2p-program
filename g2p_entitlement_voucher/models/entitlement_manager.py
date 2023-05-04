# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class G2PCryptoKeySet(models.Model):
    _inherit = "g2p.crypto.key.set"

    voucher_manager_id = fields.Many2one(
        "g2p.program.entitlement.manager.voucher", ondelete="cascade"
    )


class EntitlementManager(models.Model):
    _inherit = "g2p.program.entitlement.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = ("g2p.program.entitlement.manager.voucher", "Voucher")
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PVoucherEntitlementManager(models.Model):
    _name = "g2p.program.entitlement.manager.voucher"
    _inherit = "g2p.program.entitlement.manager.default"
    _description = "Voucher Entitlement Manager"

    # This is a one2one relation
    crypto_key_set = fields.One2many("g2p.crypto.key.set", "voucher_manager_id")

    voucher_file_config = fields.Many2one("g2p.payment.file.config")

    voucher_document_store = fields.Many2one("storage.backend", required=True)

    @api.model
    def create(self, values):
        if not values.get("crypto_key_set", None):
            values["crypto_key_set"] = [(0, 0, {})]
        return super(G2PVoucherEntitlementManager, self).create(values)

    def open_voucher_config_form(self):
        if self.voucher_file_config:
            return {
                "name": _("Payment File Config"),
                "type": "ir.actions.act_window",
                "res_id": self.voucher_file_config.id,
                "res_model": "g2p.payment.file.config",
                "view_mode": "form",
                "target": "new",
            }
        return {}

    # TODO: Later to be made async
    def approve_entitlements(self, entitlements):
        res = super(G2PVoucherEntitlementManager, self).approve_entitlements(
            entitlements
        )

        # Render all qrcodes and store for all entitlements
        for qrcode_config in self.voucher_file_config.qrcode_config_ids:
            qrcode_config.render_datas_and_store(
                "g2p.entitlement",
                entitlements.ids,
                self.crypto_key_set[0],
                res_id_field_in_qrcode_model="entitlement_id",
            )

        # Render the voucher template itself
        files = self.voucher_file_config.render_and_store(
            "g2p.entitlement", entitlements.ids, self.voucher_document_store
        )
        for i, rec in enumerate(entitlements):
            rec.voucher_document_id = files[i]

        return res
