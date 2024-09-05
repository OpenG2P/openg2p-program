import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PSocialRegistryImportedRegistrants(models.Model):
    _name = "g2p.social.registry.imported.registrants"
    _description = "Social Registry Imported Registrants"

    fetch_social_registry_id = fields.Many2one(
        "g2p.fetch.social.registry.beneficiary",
        required=True,
        auto_join=True,
    )

    registrant_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_group", "=", False), ("is_registrant", "=", True)],
        auto_join=True,
    )

    is_group = fields.Boolean()

    is_created = fields.Boolean("Created?")
    is_updated = fields.Boolean("Updated?")
