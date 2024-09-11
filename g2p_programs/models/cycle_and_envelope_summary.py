from odoo import models, fields, api

class CycleEnvelopeSummary(models.TransientModel):
    _name = "g2p.cycle.envelope.summary"
    _description = "Cycle Envelope Summary"

    # _inherit = [
    #     "g2p.cycle"
    # ]
    cycle_id = fields.Many2one("g2p.cycle", "Cycle", required=True)
    number_of_disbursements_received = fields.Integer()
    total_disbursement_amount_received = fields.Integer()
    funds_available_with_bank = fields.Char()
    funds_available_latest_timestamp= fields.Char()
    funds_available_latest_error_code= fields.Char()
    funds_available_attempts = fields.Integer()
    funds_blocked_with_bank= fields.Char()
    funds_blocked_latest_timestamp= fields.Char()
    funds_blocked_latest_error_code= fields.Char()
    funds_blocked_attempts= fields.Integer()
    funds_blocked_reference_number=fields.Char()
    id_mapper_resolution_required= fields.Boolean()
    number_of_disbursements_shipped= fields.Integer()
    number_of_disbursements_reconciled= fields.Integer()
    number_of_disbursements_reversed= fields.Integer()
