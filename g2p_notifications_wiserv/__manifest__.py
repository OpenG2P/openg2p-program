{
    "name": "G2P Notifications: Wiserv SMS Service Provider",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3.0",
    "depends": ["g2p_notifications_base", "mail"],
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "views/wiservsms_notification_manager.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [],
        "web.assets_qweb": [],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
