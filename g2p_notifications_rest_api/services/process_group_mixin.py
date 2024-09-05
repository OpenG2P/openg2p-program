from odoo.addons.component.core import AbstractComponent


class ProcessGroupMixin(AbstractComponent):
    _inherit = "process_group.rest.mixin"

    def _process_group(self, group_info):
        res = super()._process_group(group_info)
        if group_info.dict().get("notification_preference", None):
            res["notification_preference"] = group_info.notification_preference
        return res
