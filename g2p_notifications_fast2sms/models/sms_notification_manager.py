import logging

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)


class NotificationManager(models.Model):
    _inherit = "g2p.program.notification.manager"

    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.notification.manager.fast2sms",
            "Fast2SMS Notification",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class Fast2SMSNotificationManager(models.Model):
    _name = "g2p.program.notification.manager.fast2sms"
    _description = "Fast2SMS Notification Manager"
    _inherit = ["g2p.program.notification.manager.sms"]

    send_api_endpoint = fields.Char("Send API Endpoint", required=True)
    access_token = fields.Char(required=True)
    sms_language = fields.Char("SMS Language", default="english")
    sms_route = fields.Char("SMS Route", default="q")

    def send_sms(self, phone, body):
        response = requests.post(
            self.send_api_endpoint,
            data={
                "message": body,
                "language": self.sms_language,
                "route": self.sms_route,
                "numbers": phone,
            },
            headers={
                "authorization": self.access_token,
            },
            timeout=15,
        )
        return response.text
