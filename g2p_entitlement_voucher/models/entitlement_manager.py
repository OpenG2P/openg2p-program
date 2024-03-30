# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models

from odoo.addons.queue_job.delay import group

_logger = logging.getLogger(__name__)


class G2PCryptoKeySet(models.Model):
    _inherit = "g2p.crypto.key.set"

    voucher_manager_id = fields.Many2one("g2p.program.entitlement.manager.voucher", ondelete="cascade")


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

    auto_generate_voucher_on_approval = fields.Boolean(default=True)

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
        res = super(G2PVoucherEntitlementManager, self).approve_entitlements(entitlements)

        if self.auto_generate_voucher_on_approval:
            err, message, sticky, vouchers = self.generate_vouchers(entitlements)

        return res

    def generate_vouchers(self, entitlements=None):
        """Generate Voucher.

        :param entitlements: A recordset of entitlements
        :return: err, message, sticky, vouchers recordset
        """
        if not entitlements:
            entitlements = self.env["g2p.entitlement"].search(
                [("state", "=", "approved"), ("voucher_document_id", "=", False)]
            )
        else:
            entitlements = entitlements.filtered_domain(
                [("state", "=", "approved"), ("voucher_document_id", "=", False)]
            )
        entitlements_count = len(entitlements)
        cycles, cycle_entitlements_list = self._group_entitlements_by_cycle(entitlements)
        if entitlements_count < self.MIN_ROW_JOB_QUEUE:
            err_count = 0
            sticky = False
            return_list = None
            for cycle_entitlements in cycle_entitlements_list:
                cycle = cycle_entitlements[0].cycle_id
                cycle_entitlements_count = len(cycle_entitlements)
                cycle_err_count, cycle_vouchers = self._generate_vouchers(cycle_entitlements)
                err_count += cycle_err_count
                if not return_list:
                    return_list = cycle_vouchers
                else:
                    return_list += cycle_vouchers
            if err_count:
                if err_count == entitlements_count:
                    message = _(f"Failed to generate {err_count} vouchers.")
                else:
                    message = _(
                        f"{entitlements_count-err_count} Vouchers Generated. Failed to generate {err_count} vouchers."
                    )
            else:
                message = _(f"{entitlements_count} Vouchers Generated.")
            return err_count, message, sticky, return_list
        else:
            for cycle_entitlements in cycle_entitlements_list:
                cycle = cycle_entitlements[0].cycle_id
                cycle_entitlements_count = len(cycle_entitlements)
                self._generate_vouchers_async(cycle, cycle_entitlements, cycle_entitlements_count)
            return (
                -1,
                _(f"Started Voucher generation for {entitlements_count}."),
                True,
                None,
            )

    def _generate_vouchers(self, entitlements):
        # TODO: Handle errors
        err_count = 0

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

        return err_count, files

    def _generate_vouchers_async(self, cycle, entitlements, entitlements_count):
        _logger.debug("Generate vouchers asynchronously")
        cycle.message_post(body=_("Generate %s vouchers started.", entitlements_count))
        cycle.write(
            {
                "locked": True,
                "locked_reason": _("Generate vouchers for entitlements in cycle."),
            }
        )

        jobs = []
        for i in range(0, entitlements_count, self.MAX_ROW_JOB_QUEUE):
            jobs.append(self.delayable()._generate_vouchers(entitlements[i : i + self.MAX_ROW_JOB_QUEUE]))
        main_job = group(*jobs)
        main_job.on_done(self.delayable().mark_job_as_done(cycle, _("Vouchers generated.")))
        main_job.delay()
