from odoo import models

from odoo.addons.g2p_programs.models import constants


class G2PVoucherEntitlementManagerNotification(models.Model):
    _inherit = "g2p.program.entitlement.manager.voucher"

    def _generate_vouchers(self, entitlements):
        err_count, files = super()._generate_vouchers(entitlements)
        notif_managers = self.program_id.get_managers(constants.MANAGER_NOTIFICATION)
        for notif_manager in notif_managers:
            notif_manager.on_generate_voucher(entitlements)
        return err_count, files
