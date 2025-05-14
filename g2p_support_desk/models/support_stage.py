from odoo import fields, models


class SupportStage(models.Model):
    _name = "support.stage"
    _description = "Support Ticket Stage"
    _order = "sequence, id"

    name = fields.Char(string="Stage Name", required=True, translate=True)
    sequence = fields.Integer(default=10)
    is_default = fields.Boolean(string="Default Stage")
    fold = fields.Boolean(string="Folded in Kanban")
    done = fields.Boolean(string="Request Done")

    description = fields.Text(translate=True)
    team_ids = fields.Many2many("support.team", string="Teams")

    template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        domain=[("model", "=", "support.ticket")],
        help="Automatically send an email when the ticket reaches this stage.",
    )
