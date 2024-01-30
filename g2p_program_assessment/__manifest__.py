# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Program: Assessment",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_programs",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/program_membership_view.xml",
        "views/entitlement_view.xml",
        "wizard/membership_assess_wizard_view.xml",
        "wizard/create_entitlement_wizard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_program_assessment/static/src/js/g2p_assessment.js",
            "/g2p_program_assessment/static/src/scss/g2p_assessment.scss",
            # "/g2p_program_assessment/static/src/js/entitlement_amount_validation.js",
            "/g2p_program_assessment/static/src/xml/g2p_assessment_templates.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
