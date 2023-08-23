from odoo.addons.component.core import AbstractComponent


class ProcessIndividualMixin(AbstractComponent):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super(ProcessIndividualMixin, self)._process_individual(individual)
        if individual.dict().get("program_memberships", None):
            res["program_registrant_info_ids"] = self._process_registrant_info(
                individual, target_type="individual"
            )
        return res

    def _process_registrant_info(self, registrant_info, target_type=""):
        registrant_info_ids = []

        for rec in registrant_info.program_memberships:
            program_id = self.env["g2p.program"].search(
                [("name", "=", rec.name), ("target_type", "=", target_type)], limit=1
            )
            if program_id:
                program_reg_info = rec.dict().get("program_registrant_info", None)
                if program_reg_info:
                    registrant_info_ids.append(
                        (
                            0,
                            0,
                            {
                                "program_id": program_id.id,
                                "state": "active",
                                "program_registrant_info": program_reg_info,
                            },
                        )
                    )
        return registrant_info_ids
