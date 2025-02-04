from odoo import api, fields, models


class G2PCycleInherited(models.Model):
    _inherit = "g2p.cycle"

    inclusion_limit = fields.Integer(default=0)
    eligibility_domain = fields.Text(string="Domain", default="[]")
    is_not_disbursement = fields.Boolean(string="Not Disbursement", default=True)
    sorting_criteria_ids = fields.One2many("g2p.sorting.criteria", "cycle_id", string="Sorting Order")

    @api.model
    def create(self, vals):
        if "program_id" in vals:
            program = self.env["g2p.program"].browse(vals["program_id"])
            if program.program_managers.manager_ref_id:
                vals[
                    "is_not_disbursement"
                ] = not program.program_managers.manager_ref_id.is_disbursement_through_priority_list
        return super().create(vals)
