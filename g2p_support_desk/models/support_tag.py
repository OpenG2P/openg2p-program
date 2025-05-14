from odoo import fields, models


class SupportTag(models.Model):
    _name = "support.tag"
    _description = "Support Ticket Tag"

    name = fields.Char(string="Tag Name", required=True)
    color = fields.Integer(string="Color Index")
    active = fields.Boolean(default=True)
