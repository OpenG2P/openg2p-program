from odoo import fields, models


class SupportTeam(models.Model):
    _name = "support.team"
    _description = "Support Team"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Team Name", required=True)
    leader_id = fields.Many2one("res.users", string="Team Leader", tracking=True)
    member_ids = fields.Many2many("res.users", string="Team Members")
    description = fields.Text()

    ticket_ids = fields.One2many("support.ticket", "team_id", string="Tickets")
    ticket_count = fields.Integer(compute="_compute_ticket_count", string="Tickets Count")

    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color Index")

    def _compute_ticket_count(self):
        for team in self:
            team.ticket_count = len(team.ticket_ids)
