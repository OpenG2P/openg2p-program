# Part of openG2P. See LICENSE file for full copyright and licensing details.

{
    "name": "OpenG2P Social Registry Importer",
    "category": "G2P",
    "summary": "Import records from Social Registry",
    "version": "17.0.0.0.0",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_programs",
        "g2p_registry_membership",
        "spp_registry_data_source",
    ],
    "data": [
        "data/ir_config_params.xml",
        "data/social_registry_data_source.xml",
        "data/search_criteria.xml",
        "security/ir.model.access.csv",
        "views/fetch_social_registry_beneficiary_views.xml",
    ],
    "external_dependencies": {"python": ["camel_converter"]},
    "application": True,
    "auto_install": False,
    "installable": True,
}
