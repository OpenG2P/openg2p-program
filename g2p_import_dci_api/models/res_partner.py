from odoo import api, fields, models


class OpenG2PRegistry(models.Model):
    # Applicable to both Individual and Group Registry

    _inherit = "res.partner"

    data_source_id = fields.Many2one(
        "spp.data.source",
        readonly=True,
    )

    ind_is_imported_from_social_registry = fields.Boolean(
        "Imported from Social Registry",
        compute="_compute_ind_is_imported_from_social_registry",
    )

    social_registry_import_ids = fields.One2many(
        "g2p.social.registry.imported.individuals",
        "individual_id",
        "Social Registry Import",
    )

    @api.depends("social_registry_import_ids")
    def _compute_ind_is_imported_from_social_registry(self):
        for rec in self:
            if rec.social_registry_import_ids:
                rec.ind_is_imported_from_social_registry = True
            else:
                rec.ind_is_imported_from_social_registry = False
