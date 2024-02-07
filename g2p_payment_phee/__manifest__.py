# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Program Payment (Payment Hub EE)",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "base",
        "g2p_registry_base",
        "g2p_programs",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_manager_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
