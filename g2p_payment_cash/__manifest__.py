# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Program Payment: Cash",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_programs",
        "g2p_payment_files",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_manager_view.xml",
        "views/entitlement_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_payment_cash/static/src/js/payment_refresh.js",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
