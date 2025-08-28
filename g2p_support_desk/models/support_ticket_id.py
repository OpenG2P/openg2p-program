from odoo import fields, models


class SupportTicketID(models.Model):
    _name = "support.ticket.id"
    _description = "Support Ticket ID"
    _order = "id desc"

    ticket_id = fields.Many2one(
        "support.ticket",
        string="Support Ticket",
        required=True,
        index=True,
        ondelete="cascade",
    )
    id_type = fields.Char(string="ID Type", size=100)
    value = fields.Char(string="ID Value", size=100)
