from odoo.addons.component.core import AbstractComponent


class ProcessGroupMixin(AbstractComponent):
    _inherit = "process_group.rest.mixin"

    def _process_group(self, group_info):
        res = super(ProcessGroupMixin, self)._process_group(group_info)
        if group_info.dict().get("program_memberships", None):
            res["program_membership_ids"] = self._process_memberships(
                group_info, target_type="group"
            )
        return res
