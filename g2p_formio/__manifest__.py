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
    "depends": ["formio", "g2p_programs", "formio_storage_filestore"],
    "data": [
        "views/formio_builder.xml",
        "views/program_view.xml",
        "wizard/g2p_self_service_program_view_wizard.xml",
    ],
    "external_dependencies": {"python": ["formio-data"]},
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
