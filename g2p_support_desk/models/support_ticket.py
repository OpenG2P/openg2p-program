import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SupportTicket(models.Model):
    _name = "support.ticket"
    _description = "Support Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, id desc"

    name = fields.Char(string="Subject", required=True, tracking=True)
    number = fields.Char(string="Ticket Number")
    description = fields.Html()
    team_id = fields.Many2one(
        "support.team",
        string="Team",
        tracking=True,
    )
    program_id = fields.Many2one(
        "g2p.program",
        string="Program",
        tracking=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        default=lambda self: self.env.user,
        tracking=True,
        domain=[("share", "=", False)],
    )

    beneficiary_id = fields.Many2one("g2p.program_membership", string="Beneficiary", tracking=True)
    # partner_email = fields.Char(string='Beneficiary Email')
    # partner_phone = fields.Char(string='Beneficiary Phone')

    category_id = fields.Many2one("support.category", string="Category")
    tag_ids = fields.Many2many("support.tag", string="Tags")
    stage_id = fields.Many2one(
        "support.stage",
        string="Stage",
        tracking=True,
        # default=lambda self: self._get_default_stage(),
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

    # Statistics
    # response_time = fields.Float(
    #     string="Response Time (Hours)", readonly=True, compute="_compute_response_time", store=True
    # )
    resolution_message = fields.Html()
    resolution_time = fields.Float(string="Resolution Time (Hours)")

    def action_assign_to_me(self):
        self.ensure_one()
        self.user_id = self.env.user.id

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "number" in fields_list and "number" not in res:
            res["number"] = self.env["ir.sequence"].next_by_code("support.ticket") or "New"
        return res

    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     if self.partner_id:
    #         self.partner_email = self.partner_id.email or False
    #         self.partner_phone = self.partner_id.phone or False
    #     else:
    #         self.partner_email = False
    #         self.partner_phone = False

    # @api.onchange('stage_id')
    # def _onchange_stage_id(self):
    #     if not self.stage_id:
    #         return
    #     if self.stage_id.done:
    #         self.closed_date = fields.Datetime.now()
    #     else:
    #         self.closed_date = False

    # @api.depends("create_date", "write_date")
    # def _compute_response_time(self):
    #     for ticket in self:
    #         if ticket.create_date and ticket.write_date:
    #             delta = ticket.write_date - ticket.create_date
    #             # Ensure we have a positive time difference
    #             if delta.total_seconds() > 0:
    #                 ticket.response_time = delta.total_seconds() / 3600.0  # Convert to hours
    #             else:
    #                 # If write_date is not after create_date, use a small positive value
    #                 ticket.response_time = 0.1
    #         else:
    #             ticket.response_time = 0.0

    @api.onchange("program_id")
    def _onchange_program_id(self):
        self.beneficiary_id = False
