# Part of openG2P. See LICENSE file for full copyright and licensing details.

{
    "name": "G2P ODK Importer: Program",
    "category": "Connector",
    "summary": "Import records from ODK and add then into Program",
    "version": "17.0.0.0.0",
    "sequence": 3,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3.0",
    "depends": ["g2p_odk_importer", "g2p_program_registrant_info"],
    "data": [
        "views/odk_import_views.xml",
    ],
    "external_dependencies": {},
    "application": True,
    "installable": True,
    "auto_install": False,
}
