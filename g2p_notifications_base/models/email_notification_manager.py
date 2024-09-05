import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class EmailNotificationManager(models.Model):
    _name = "g2p.program.notification.manager.email"
    _description = "Email Notification Manager"
    _inherit = ["g2p.base.program.notification.manager", "g2p.manager.source.mixin"]

    notification_types = ("email", "both")

    send_immediately = fields.Boolean(default=False)

    on_enrolled_in_program_template = fields.Many2one("mail.template")
    on_cycle_started_template = fields.Many2one("mail.template")
    on_cycle_ended_template = fields.Many2one("mail.template")
    on_otp_send_template = fields.Many2one("mail.template")
    on_payment_send_template = fields.Many2one("mail.template")

    def on_enrolled_in_program(self, program_memberships):
        if not self.on_enrolled_in_program_template:
            return
        # TODO: Make the following asynchrous and in bulk
        for mem in program_memberships:
            if mem.partner_id.notification_preference in self.notification_types and mem.partner_id.email:
                self.on_enrolled_in_program_template.send_mail(mem.id, force_send=self.send_immediately)

    def on_otp_send(self, otp=None, email=None, **data):
        if not self.on_otp_send_template:
            return
        # TODO: Make the following asynchrous and in bulk
        if otp and email:
            data["otp"] = otp
            data["email"] = email
            mail_values = self.on_otp_send_template.generate_email(
                self.id,
                [
                    "subject",
                    "email_from",
                    "reply_to",
                    "email_cc",
                ],
            )
            mail_values["email_to"] = email
            mail_values["body_html"] = self.on_otp_send_template._render_template(
                self.on_otp_send_template.body_html,
                self._name,
                [
                    self.id,
                ],
                add_context=data,
                engine="qweb",
            )[self.id]
            mail = self.env["mail.mail"].create(mail_values)
            mail.send()
            return mail
        return None

    def on_payment_send(self, batch):
        if not self.on_payment_send_template:
            return

        payments_to_notify = [
            payment
            for payment in batch.payment_ids
            if payment.status in ("paid",) and not payment.is_payment_notification_sent
        ]

        for res in payments_to_notify:
            if res.partner_id.notification_preference in self.notification_types and res.partner_id.email:
                self.on_payment_send_template.send_mail(res.id, force_send=self.send_immediately)
                res.is_payment_notification_sent = True

    def on_cycle_started(self, program_memberships, cycle_id):
        if not self.on_cycle_started_template:
            return
        # TODO: to be implemented
        return

    def on_cycle_ended(self, program_memberships, cycle_id):
        if not self.on_cycle_ended_template:
            return
        # TODO: to be implemented
        return
