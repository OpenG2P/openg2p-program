{
    "name": "OpenG2P Theme",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3.0",
    "depends": ["base", "web", "auth_signup", "website"],
    "data": [
        "templates/g2p_login_page.xml",
        "templates/g2p_reset_password.xml",
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_theme/static/src/js/g2p_window_title.js",
            "g2p_theme/static/src/css/style.css",
        ],
        "web.assets_frontend": [
            "g2p_theme/static/src/scss/new_login_page.scss",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
