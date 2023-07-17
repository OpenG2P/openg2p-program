# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class G2PProgramMembershipAssessmentWizard(models.TransientModel):
    _name = "g2p.program_membership.assessment.wizard"
    _description = "G2P Program Membership Assessment Wizard"
    _order = "id asc"

    program_membership_id = fields.Many2one("g2p.program_membership")
