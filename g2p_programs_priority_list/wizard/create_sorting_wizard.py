from odoo import fields, models


class CycleCreationWizardCriteria(models.TransientModel):
    _name = "cycle.creation.wizard.criteria"
    _description = "Temporary Sorting Criteria for Cycle Creation Wizard"

    wizard_id = fields.Many2one("cycle.creation.wizard", string="Wizard", ondelete="cascade")
    field_name = fields.Many2one(
        "ir.model.fields",
        domain="[('model', '=', 'res.partner')]",
        help="Select a field from res.partner for sorting",
    )
    order = fields.Selection([("asc", "Ascending"), ("desc", "Descending")], required=True)
    sequence = fields.Integer()
