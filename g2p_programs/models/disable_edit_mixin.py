# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import models, fields

class DisableEditMixin(models.AbstractModel):
    """Disable Edit Mixin."""

    _name = "disable.edit.mixin"
    _description = "Disable Edit Option"

    edit_css = fields.Html(
        sanitize=False,
        compute="_compute_css",
    )

    def _compute_css(self):
        # Add your dynamic computation logic here
        for rec in self:
            rec.edit_css = False

