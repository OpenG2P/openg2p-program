from odoo.addons.component.core import AbstractComponent


class ProcessIndividualMixin(AbstractComponent):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super(ProcessIndividualMixin, self)._process_individual(individual)
        if individual.dict().get("program_registrant_info", None):
            res["program_registrant_info_ids"] = self._process_registrant_info(
                individual
            )
        return res

    def _process_registrant_info(self, individual):
        memberships = individual.dict().get("program_memberships", None)
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
                        "program_id": program_id.id,
                        "program_registrant_info": individual.dict().get(
                            "program_registrant_info", None
                        ),
                    },
                )
            )

        return registrant_info_ids
