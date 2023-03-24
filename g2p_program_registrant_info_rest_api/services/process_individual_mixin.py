from odoo.addons.component.core import AbstractComponent


class ProcessIndividualMixin(AbstractComponent):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super(ProcessIndividualMixin, self)._process_individual(individual)
        print("Result")
        print(res)
        res.program_registrant_info_ids = self._process_registrant_info(individual)
        return res

    def _process_registrant_info(self, individual):
        mmemberships = individual.dict().get("program_memberships", None)
        registrant_info_ids = []
        for program_membership in mmemberships:
            program_id = self.env["g2p.program"].search(
                [("name", "=", program_membership)], limit=1
            )
            registrant_info_ids.append(({"registrant":program_id, "program_registrant_info":individual.dict().get("program_registrant_info", None)}))
            print(program_id)
            
        return registrant_info_ids