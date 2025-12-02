from odoo import api, fields, models


class SupportTicket(models.Model):
    _name = "support.ticket"
    _description = "Support Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, id desc"

    name = fields.Char(string="Subject", required=True, tracking=True)
    number = fields.Char(string="Ticket Number", default="New")
    description = fields.Html()
    team_id = fields.Many2one(
        "support.team",
        string="Team",
        tracking=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        default=lambda self: self.env.user,
        tracking=True,
        domain=[("share", "=", False)],
    )

    category_id = fields.Many2one("support.category", string="Category")
    tag_ids = fields.Many2many("support.tag", string="Tags")
    stage_id = fields.Many2one(
        "support.stage",
        string="Stage",
        tracking=True,
        copy=False,
        required=True,
    )
    priority = fields.Selection(
        [("0", "Low"), ("1", "Medium"), ("2", "High"), ("3", "Urgent")],
        default="1",
        tracking=True,
    )
    color = fields.Integer(string="Color Index")
    active = fields.Boolean(default=True)

    closed_date = fields.Datetime()

    resolution_message = fields.Html()
    resolution_time = fields.Float(string="Resolution Time (Hours)")

    program_id = fields.Char(string="Program ID")
    ern = fields.Char(string="Entitlement Reference Number")
    application_id = fields.Char(string="Application ID")

    creator_name = fields.Char()
    creator_email = fields.Char()
    creator_address = fields.Text()
    creator_phone = fields.Char()

    reg_ids = fields.One2many(
        "support.ticket.id",
        "ticket_id",
        string="IDs",
    )

    def action_assign_to_me(self):
        self.ensure_one()
        self.user_id = self.env.user.id

    @api.model
    def create(self, vals):
        if vals.get("number", "New") == "New":
            vals["number"] = self.env["ir.sequence"].next_by_code("support.ticket") or "New"
        return super().create(vals)
