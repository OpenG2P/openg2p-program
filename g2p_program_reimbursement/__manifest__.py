# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Programs: Reimbursement",
    "category": "G2P",
    "version": "15.0.1.1.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Production/Stable",
    "depends": [
        "g2p_programs",
        # TODO: The following need not be a dependency
        "g2p_program_assessment",
    ],
    "data": [
        "views/program_view.xml",
        "views/cycle_view.xml",
        "views/entitlement_view.xml",
        "wizard/assign_to_program_wizard.xml",
        "wizard/create_program_wizard.xml",
        "wizard/create_entitlement_wizard.xml",
    ],
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
