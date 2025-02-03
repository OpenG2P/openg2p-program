# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class CycleCreationWizard(models.TransientModel):
    _name = "cycle.creation.wizard"
    _description = "Cycle Creation Wizard"

    cycle_id = fields.Many2one("g2p.cycle", string="Cycle", readonly=True)
    name = fields.Char(string="Cycle Name", required=True, readonly=True)
    program_id = fields.Many2one("g2p.program", string="Program", required=True, readonly=True)

    inclusion_limit = fields.Integer(default=0)
    eligibility_domain = fields.Text(string="Domain", default="[]")

    sorting_criteria_ids = fields.One2many(
        "cycle.creation.wizard.criteria", "wizard_id", string="Sorting Order"
    )

    def action_confirm(self):
        if self.cycle_id:
            sorting_criteria = self.sorting_criteria_ids
            cycle_sorting_criteria = self.cycle_id.sorting_criteria_ids

            # Store existing field names to check which ones are removed
            new_field_names = sorting_criteria.mapped("field_name.id")

            for criterion in sorting_criteria:
                existing_criteria = cycle_sorting_criteria.filtered(
                    lambda c: c.field_name.id == criterion.field_name.id
                )

                if existing_criteria:
                    existing_criteria.write(
                        {
                            "order": criterion.order,
                            "sequence": criterion.sequence,
                        }
                    )
                else:
                    self.env["g2p.sorting.criteria"].create(
                        {
                            "cycle_id": self.cycle_id.id,
                            "field_name": criterion.field_name.id,
                            "order": criterion.order,
                            "sequence": criterion.sequence,
                        }
                    )

            # Remove criteria that are no longer in sorting_criteria
            to_remove = cycle_sorting_criteria.filtered(lambda c: c.field_name.id not in new_field_names)
            if to_remove:
                to_remove.unlink()

            self.cycle_id.write(
                {"inclusion_limit": self.inclusion_limit, "eligibility_domain": self.eligibility_domain}
            )

            self.cycle_id.copy_beneficiaries_from_program()
        return {"type": "ir.actions.act_window_close"}
