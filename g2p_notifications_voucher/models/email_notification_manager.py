import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class EmailNotificationManager(models.Model):
    _inherit = "g2p.program.notification.manager.email"

    on_generate_voucher_template = fields.Many2one("mail.template")

    def on_generate_voucher(self, entitlements):
        if not self.on_generate_voucher_template:
            return
        # TODO: Make the following asynchrous and in bulk
        for entitlement in entitlements:
            if entitlement.partner_id.email:
                self.on_generate_voucher_template.send_mail(entitlement.id, force_send=self.send_immediately)
