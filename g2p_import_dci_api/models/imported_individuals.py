import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PSocialRegistryImportedIndividuals(models.Model):
    _name = "g2p.social.registry.imported.individuals"
    _description = "Social Registry Imported Individuals"

    fetch_social_registry_id = fields.Many2one(
        "g2p.fetch.social.registry.beneficiary",
        required=True,
        auto_join=True,
    )

    individual_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_group", "=", False), ("is_registrant", "=", True)],
        auto_join=True,
    )

    is_created = fields.Boolean("Created?")
    is_updated = fields.Boolean("Updated?")
