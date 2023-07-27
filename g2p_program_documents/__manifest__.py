# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Program: Documents",
    "category": "G2P",
    "version": "15.0.1.1.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_documents",
        "g2p_programs",
    ],
    "data": [
        "security/program_documents_security.xml",
        "views/programs_view.xml",
        "views/program_membership_view.xml",
        "views/entitlement_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_program_documents/static/src/js/preview_document.js",
        ],
        "web.assets_qweb": [
            "/g2p_program_documents/static/src/xml/preview_document_view.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
