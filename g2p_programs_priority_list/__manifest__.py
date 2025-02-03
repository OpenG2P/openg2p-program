{
    "name": "OpenG2P Programs Priority List",
    "category": "G2P/G2P",
    "version": "17.0.1.2.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_programs"],
    "data": [
        "security/ir.model.access.csv",
        "views/cycle_view.xml",
        "views/program_manager_view.xml",
        "views/cycle_manager_view.xml",
        "views/cycle_membership_view.xml",
        "wizard/create_cycle_wizard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_programs_priority_list/static/src/css/style.css",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
