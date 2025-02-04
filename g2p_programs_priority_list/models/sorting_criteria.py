from odoo import fields, models


class SortingCriteria(models.Model):
    _name = "g2p.sorting.criteria"
    _description = "Sorting Criteria"

    cycle_id = fields.Many2one("g2p.cycle", string="Cycle")
    manager_id = fields.Many2one("g2p.cycle.manager.default", string="Cycle Manager")

    sequence = fields.Integer()
    field_name = fields.Many2one(
        "ir.model.fields",
        domain="[('model', '=', 'res.partner')]",
        help="Select a field from res.partner for sorting",
    )
    order = fields.Selection([("asc", "Ascending"), ("desc", "Descending")], required=True)
