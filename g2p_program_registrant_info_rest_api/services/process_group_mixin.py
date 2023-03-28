from odoo.addons.component.core import AbstractComponent


class ProcessGroupMixin(AbstractComponent):
    _inherit = "process_group.rest.mixin"

    def _process_group(self, group_info):
        res = super(ProcessGroupMixin, self)._process_group(group_info)
        if group_info.dict().get("program_registrant_info", None):
            res["program_registrant_info_ids"] = self._process_registrant_info(
                group_info
            )
        return res

    def _process_registrant_info(self, group_info):
        memberships = group_info.dict().get("program_memberships", None)
        registrant_info_ids = []
        for program_membership in memberships:
            program_id = self.env["g2p.program"].search(
                [("name", "=", program_membership["name"])], limit=1
            )
            registrant_info_ids.append(
                (
                    0,
                    0,
                    {
                        "program": program_id.id,
                        "program_registrant_info": group_info.dict().get(
                            "program_registrant_info", None
                        ),
                    },
                )
            )

        return registrant_info_ids
