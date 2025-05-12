from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SupportTicket(models.Model):
    _name = 'support.ticket'
    _description = 'Support Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, id desc'

    name = fields.Char(string='Subject', required=True, tracking=True)
    number = fields.Char(string='Ticket Number', readonly=True, default='New', copy=False)
    description = fields.Html(string='Description')
    print("*****description****", description)
    team_id = fields.Many2one(
        'support.team', 
        string='Team', 
        tracking=True,
        default=lambda self: self._get_default_team()
    )
    print("*****team_id****", team_id)
    program_id = fields.Many2one(
        'g2p.program', 
        string='Program', 
        tracking=True,
        default=lambda self: self._get_default_program()
    )
    print("*****program_id****", program_id)
    user_id = fields.Many2one(
        'res.users', string='Assigned To',
        default=lambda self: self.env.user,
        tracking=True,
        domain=[('share', '=', False)]
    )
    print("*****user_id****", user_id)
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Beneficiary',
        tracking=True
    )
    program_beneficiary_ids = fields.Many2many(
        'res.partner',
        string='Program Beneficiaries',
        compute='_compute_program_beneficiaries',
        store=True
    )
    # partner_email = fields.Char(string='Beneficiary Email')
    # partner_phone = fields.Char(string='Beneficiary Phone')
    
    category_id = fields.Many2one('support.category', string='Category')
    print("*****category_id****", category_id)
    tag_ids = fields.Many2many('support.tag', string='Tags')
    print("*****tag_ids****", tag_ids)
    stage_id = fields.Many2one(
        'support.stage',
        string='Stage',
        tracking=True,
        default=lambda self: self._get_default_stage(),
        copy=False,
        required=True
    )
    print("*****stage_id****", stage_id)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)
    print("*****priority****", priority)
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked')
    ], string='Kanban State', default='normal', tracking=True)
    print("*****kanban_state****", kanban_state)
    color = fields.Integer(string='Color Index')
    print("*****color****", color)
    active = fields.Boolean(default=True)
    print("*****active****", active)
    
    # Dates
    create_date = fields.Datetime('Creation Date', readonly=True)
    print("*****create_date****", create_date)
    write_date = fields.Datetime('Last Update', readonly=True)
    print("*****write_date****", write_date)
    closed_date = fields.Datetime('Closed Date', readonly=True)
    print("*****closed_date****", closed_date)
    
    # Statistics
    response_time = fields.Float(
        string='Response Time (Hours)',
        readonly=True,
        compute='_compute_response_time',
        store=True
    )
    print("*****response_time****", response_time)
    resolution_time = fields.Float(string='Resolution Time (Hours)', readonly=True)
    print("*****resolution_time****", resolution_time)

    @api.model
    def create(self, vals):
        if vals.get('number', 'New') == 'New':
            vals['number'] = self.env['ir.sequence'].next_by_code('support.ticket') or 'New'
        return super(SupportTicket, self).create(vals)

    @api.model
    def _get_default_stage(self):
        try:
            stage = self.env['support.stage'].search([('is_default', '=', True)], limit=1)
            if not stage:
                # If no default stage, get the first stage
                stage = self.env['support.stage'].search([], limit=1)
            if not stage:
                raise ValidationError(_("No support stage found. Please create at least one stage."))
            return stage.id
        except Exception as e:
            _logger.error("Error getting default stage: %s", str(e))
            raise ValidationError(_("Error getting default stage: %s") % str(e))

    @api.model
    def _get_default_team(self):
        try:
            team = self.env['support.team'].search([], limit=1)
            if not team:
                raise ValidationError(_("No support team found. Please create at least one team."))
            return team.id
        except Exception as e:
            _logger.error("Error getting default team: %s", str(e))
            # raise ValidationError(_("Error getting default team: %s") % str(e))

    @api.model
    def _get_default_program(self):
        try:
            program = self.env['g2p.program'].search([], limit=1)
            if not program:
                raise ValidationError(_("No program found. Please create at least one program."))
            return program.id
        except Exception as e:
            _logger.error("Error getting default program: %s", str(e))
            # raise ValidationError(_("Error getting default program: %s") % str(e))

    def action_assign_to_me(self):
        self.ensure_one()
        self.user_id = self.env.user.id

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

    @api.depends('create_date', 'write_date')
    def _compute_response_time(self):
        for ticket in self:
            if ticket.create_date and ticket.write_date:
                delta = ticket.write_date - ticket.create_date
                # Ensure we have a positive time difference
                if delta.total_seconds() > 0:
                    ticket.response_time = delta.total_seconds() / 3600.0  # Convert to hours
                else:
                    # If write_date is not after create_date, use a small positive value
                    ticket.response_time = 0.1
            else:
                ticket.response_time = 0.0

    @api.depends('program_id')
    def _compute_program_beneficiaries(self):
        for ticket in self:
            if ticket.program_id:
                beneficiaries = self.env['g2p.program_membership'].search([
                    ('program_id', '=', ticket.program_id.id)
                ]).mapped('partner_id')
                ticket.program_beneficiary_ids = beneficiaries
            else:
                ticket.program_beneficiary_ids = False

    @api.constrains('partner_id', 'program_id')
    def _check_beneficiary_in_program(self):
        for ticket in self:
            if ticket.partner_id and ticket.program_id:
                membership = self.env['g2p.program_membership'].search([
                    ('program_id', '=', ticket.program_id.id),
                    ('partner_id', '=', ticket.partner_id.id)
                ], limit=1)
                if not membership:
                    # Clear the partner_id if the beneficiary is no longer in the program
                    ticket.partner_id = False
                    raise ValidationError(_("The selected beneficiary must be a member of the program."))

    @api.onchange('program_id')
    def _onchange_program_id(self):
        if self.program_id:
            # Update the domain for partner_id
            beneficiaries = self.env['g2p.program_membership'].search([
                ('program_id', '=', self.program_id.id)
            ]).mapped('partner_id')
            # Clear partner_id if it's not in the available beneficiaries
            if self.partner_id and self.partner_id not in beneficiaries:
                self.partner_id = False
            return {
                'domain': {
                    'partner_id': [('id', 'in', beneficiaries.ids)]
                }
            }
        else:
            # Clear partner_id when program is removed
            self.partner_id = False
            return {
                'domain': {
                    'partner_id': [('id', 'in', [])]
                }
            }

    def write(self, vals):
        # Check if we're writing program_id
        if 'program_id' in vals:
            # If we're changing the program, check if the current partner_id is valid
            if self.partner_id:
                membership = self.env['g2p.program_membership'].search([
                    ('program_id', '=', vals['program_id']),
                    ('partner_id', '=', self.partner_id.id)
                ], limit=1)
                if not membership:
                    # Clear the partner_id if the beneficiary is not in the new program
                    vals['partner_id'] = False
        return super().write(vals)
