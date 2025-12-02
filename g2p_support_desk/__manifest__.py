{
    "name": "G2P Support Desk",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "summary": "OpenG2P Support Desk Management System",
    "depends": [
        "base",
        "mail",
        "portal",
        "web",
    ],
    "data": [
        "security/support_desk_security.xml",
        "security/ir.model.access.csv",
        "views/support_ticket_views.xml",
        "views/support_team_views.xml",
        "views/support_category_views.xml",
        "views/support_tag_views.xml",
        "views/support_stage_views.xml",
        "views/menu_views.xml",
        "data/support_desk_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_support_desk/static/src/css/style.css",
        ],
    },
    "demo": [
        "demo/helpdesk_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
}
