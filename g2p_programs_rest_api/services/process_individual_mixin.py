from odoo.addons.component.core import AbstractComponent


class ProcessIndividualMixin(AbstractComponent):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super(ProcessIndividualMixin, self)._process_individual(individual)
        if individual.dict().get("program_memberships", None):
            res["program_membership_ids"] = self._process_memberships(
                individual, target_type="individual"
            )
        return res

    def _process_memberships(self, registrant_info, target_type=""):
        prog_members = []
        for rec in registrant_info.program_memberships:
            program_id = self.env["g2p.program"].search(
                [("name", "=", rec.name), ("target_type", "=", target_type)], limit=1
            )
            if program_id:
                prog_mem_dict = {}
                prog_mem_dict["program_id"] = program_id.id
                # Hardcoding the following to draft now. TODO: change the state later.
                prog_mem_dict["state"] = "draft"
                if rec.enrollment_date:
                    prog_mem_dict["enrollment_date"] = rec.enrollment_date

                prog_members.append((0, 0, prog_mem_dict))
        return prog_members
