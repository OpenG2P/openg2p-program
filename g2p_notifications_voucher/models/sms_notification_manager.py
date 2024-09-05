from odoo import fields, models


class SMSNotificationManager(models.Model):
    _inherit = "g2p.program.notification.manager.sms"

    on_generate_voucher_template = fields.Many2one("sms.template")

    def on_generate_voucher(self, entitlements):
        if not self.on_generate_voucher_template:
            return
        # TODO: Make the following asynchrous and in bulk
        send_sms_body_list = self.on_generate_voucher_template._render_template(
            self.on_generate_voucher_template.body,
            "g2p.entitlement",
            [ent.id for ent in entitlements],
            engine="inline_template",
        )
        for ent in entitlements:
            self.send_sms(ent.partner_id.phone, send_sms_body_list.get(ent.id, None))
