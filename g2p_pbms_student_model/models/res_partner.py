# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    ##########################
    ##      Student Info    ##
    ##########################

    institution_name = fields.Selection(
        [
            ("UCT", "University of Cape Town"),
            ("SIT", "Stellenbosch Institute of Technology"),
            ("DCE", "Durban College of Engineering"),
        ]
    )

    year_of_study = fields.Selection(
        [("1", "1st Year"), ("2", "2nd Year"), ("3", "3rd Year"), ("4", "4th Year")]
    )

    course_name = fields.Selection(
        [
            ("cs", "Computer Science"),
            ("ec", "Electrical Engineering"),
            ("me", "Mechanical Engineering"),
            ("ce", "Civil Engineering"),
            ("fa", "Financial Accounting"),
            ("mm", "Marketing Management"),
            ("scl", "Supply Chain & Logistics"),
            ("bt", "Biotechnology"),
            ("es", "Environmental Science"),
            ("pse", "Polymer Science"),
        ]
    )
    qualification_type = fields.Selection(
        [("cerficiate", "Certificate"), ("diploma", "Diploma"), ("degree", "Degree")]
    )
    duration_of_course = fields.Char()
    previous_nsfas_beneficiary = fields.Selection([("yes", "Yes"), ("no", "No")])

    ##########################
    ## Parent/Guardian Info ##
    ##########################

    guardian_name = fields.Char()
    guardian_id = fields.Char()
    household_income = fields.Selection(
        [
            ("below_122000", "Below R122,000"),
            ("122000_to_350000", "R122,000 - R350,000"),
            ("above_350000", "Above R350,000"),
        ]
    )
    guardian_employment_status = fields.Selection([("employed", "Employed"), ("unemployed", "Unemployed")])
    number_of_dependents = fields.Integer()
    accommodation_type = fields.Selection(
        [("owned", "Owned"), ("rented", "Rented"), ("informal", "Informal Settlement")]
    )
