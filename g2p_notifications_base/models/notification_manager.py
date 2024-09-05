from odoo import models


class NotificationManager(models.Model):
    _inherit = "g2p.program.notification.manager"

    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = ("g2p.program.notification.manager.email", "Email Notification")
        if new_manager not in selection:
            selection.append(new_manager)
        return selection
