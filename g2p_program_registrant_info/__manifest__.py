{
    "name": "G2P Program: Registrant Info",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_registry_base",
        "g2p_registry_individual",
        "g2p_registry_group",
        "g2p_programs",
    ],
    "data": [
        "views/program_registrant_info.xml",
        "views/program_membership.xml",
        "wizard/g2p_program_registrant_info_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_program_registrant_info/static/src/js/g2p_additional_info.js",
        ],
        "web.assets_common": [
            "/g2p_program_registrant_info/static/src/xml/g2p_additional_info.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
