# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class G2PResPartnerInherited(models.Model):
    _inherit = "res.partner"

    #######################################################
    #####          Social Status Information          #####
    #######################################################

    num_preg_lact_women = fields.Integer()
    num_malnourished_children = fields.Integer()
    num_disabled = fields.Integer()
    type_of_disability = fields.Selection(
        [
            ("visual_impairment", "Visual Impairment"),
            ("hearing_impairment", "Hearing Impairment"),
            ("physical_disability", "Physical Disability"),
            ("cognitive_disability", "Cognitive Disability"),
        ]
    )
    caste_ethnic_group = fields.Selection(
        [
            ("bantu", "Bantu"),
            ("nilotic", "Nilotic"),
            ("afro_asian", "Afro-Asiatic"),
            ("khoisan", "Khoisan"),
            ("pygmy", "Pygmy"),
            ("other", "Other"),
        ],
    )
    belong_to_protected_groups = fields.Selection([("yes", "Yes"), ("no", "No")])
    other_vulnerable_status = fields.Selection([("yes", "Yes"), ("no", "No")])

    #######################################################
    #####              Household Details              #####
    #######################################################

    education_level = fields.Selection(
        [
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("higher_secondary", "Higher Secondary"),
            ("bachelors", "Bachelors"),
            ("masters", "Masters"),
        ]
    )
    employment_status = fields.Selection(
        [
            ("employed_full", "Employed - Full Time"),
            ("employed_part", "Employed - Part Time"),
            ("self_employed", "Self-employed"),
            ("unemployed", "Unemployed"),
        ]
    )
    marital_status = fields.Selection(
        [("single", "Single"), ("married", "Married"), ("divorced", "divorced")]
    )

    #######################################################
    #####         Economic Status Information         #####
    #######################################################

    income_sources = fields.Selection(
        [
            ("agriculture", "Agriculture"),
            ("business", "Business"),
            ("mining", "Mining"),
            ("manufacturing", "Manufacturing"),
            ("construction", "Construction"),
        ]
    )
    # Income field was of INT type and it has validation which will cause the errors.
    annual_income = fields.Selection(
        [("below_5000", "Below 5000"), ("5001_10000", "5001-10,000"), ("above_10000", "Above 10,000")],
    )
    owns_two_wheeler = fields.Selection([("yes", "Yes"), ("no", "No")])
    owns_three_wheeler = fields.Selection([("yes", "Yes"), ("no", "No")])
    owns_four_wheeler = fields.Selection([("yes", "Yes"), ("no", "No")])
    owns_cart = fields.Selection([("yes", "Yes"), ("no", "No")])
    land_ownership = fields.Selection([("yes", "Yes"), ("no", "No")])
    type_of_land_owned = fields.Selection(
        [
            ("agricultural", "Agricultural Land"),
            ("residential", "Residential Land"),
            ("pastoral", "Pastoral Land"),
            ("forest", "Forest Land"),
            ("commercial", "Commercial Land"),
            ("communal", "Communal Land"),
            ("other", "Other"),
        ]
    )
    land_size = fields.Float()
    owns_house = fields.Selection([("yes", "Yes"), ("no", "No")])
    owns_livestock = fields.Selection([("yes", "Yes"), ("no", "No")])

    #######################################################
    #####        Housing Condition Information        #####
    #######################################################

    housing_type = fields.Selection(
        [("permanent", "Permanent"), ("temporary", "Temporary")], "Type of Housing"
    )
    house_condition = fields.Selection([("mud", "Mud"), ("cement", "Cement")])
    sanitation_condition = fields.Selection([("yes", "Yes"), ("no", "No")])
    water_access = fields.Selection([("yes", "Yes"), ("no", "No")])
    electricity_access = fields.Selection([("yes", "Yes"), ("no", "No")])

    #######################################################
    #####               Computed Fields               #####
    #######################################################

    is_hh_unemployed = fields.Boolean(compute="_compute_hh_is_unemployed", store=True)

    @api.constrains("group_membership_ids", "employment_status")
    def _compute_hh_is_unemployed(self):
        for rec in self:
            group_head = self.env["g2p.group.membership"].get_household_head(rec)
            if group_head:
                rec.is_hh_unemployed = group_head.employment_status == "unemployed"
            else:
                rec.is_hh_unemployed = False
