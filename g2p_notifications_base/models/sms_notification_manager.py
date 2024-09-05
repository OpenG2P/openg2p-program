from odoo import fields, models


class SMSNotificationManager(models.Model):
    _inherit = "g2p.program.notification.manager.sms"

    notification_types = ("sms", "both")

    on_enrolled_in_program_template = fields.Many2one("sms.template")
    on_cycle_started_template = fields.Many2one("sms.template")
    on_cycle_ended_template = fields.Many2one("sms.template")
    on_otp_send_template = fields.Many2one("sms.template")
    on_payment_send_template = fields.Many2one("sms.template")

    def on_enrolled_in_program(self, program_memberships):
        if not self.on_enrolled_in_program_template:
            return
        # TODO: Make the following asynchrous and in bulk
        send_sms_body_list = self.on_enrolled_in_program_template._render_template(
            self.on_enrolled_in_program_template.body,
            "g2p.program_membership",
            [mem.id for mem in program_memberships],
            engine="inline_template",
        )
        for mem in program_memberships:
            self.send_sms_to_membership(mem, send_sms_body_list.get(mem.id, None))

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

    def on_otp_send(self, otp=None, phone=None, **data):
        if not self.on_otp_send_template:
            return
        # TODO: Make the following asynchrous and in bulk
        if otp and phone:
            data["otp"] = otp
            data["phone"] = phone
            body = self.on_otp_send_template._render_template(
                self.on_otp_send_template.body,
                self._name,
                [
                    self.id,
                ],
                add_context=data,
                engine="inline_template",
            )[self.id]
            return self.send_sms(phone, body)
        return None

    def send_sms_to_membership(self, membership, body):
        if (
            membership.partner_id.notification_preference in self.notification_types
            and membership.partner_id.phone
            and body
        ):
            return self.send_sms(membership.partner_id.phone, body)
        return None

    def on_payment_send(self, batch):
        if not self.on_payment_send_template:
            return

        # TODO: to be implemented
        return

    def send_sms(self, phone, body):
        # TODO: To be Implemented.
        raise NotImplementedError()
