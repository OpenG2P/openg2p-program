# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Formio",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "summary": "Form builders allow you to create, manage, and use dynamic forms with ease.",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "formio",
        "g2p_programs",
        "formio_storage_filestore",
        "g2p_program_registrant_info",
        "g2p_program_reimbursement",
        "g2p_program_documents",
    ],
    "data": [
        "data/formio_default_js_option.xml",
        "views/formio_builder.xml",
        "views/program_view.xml",
        "wizard/g2p_self_service_program_view_wizard.xml",
    ],
    "external_dependencies": {"python": ["formio-data"]},
    "assets": {
        "web.assets_backend": [
            # builder
            "g2p_formio/static/src/scss/formio_builder.scss",
        ],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": True,
}
