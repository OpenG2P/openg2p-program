from odoo import fields, models


class SupportCategory(models.Model):
    _name = 'support.category'
    _description = 'Support Ticket Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    parent_id = fields.Many2one('support.category', string='Parent Category')
    child_ids = fields.One2many('support.category', 'parent_id', string='Child Categories')
    active = fields.Boolean(default=True)
    
    ticket_ids = fields.One2many('support.ticket', 'category_id', string='Tickets')
    ticket_count = fields.Integer(compute='_compute_ticket_count', string='Tickets Count')

    def _compute_ticket_count(self):
        for category in self:
            category.ticket_count = len(category.ticket_ids)
