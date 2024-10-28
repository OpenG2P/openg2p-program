# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class WebsitePage(models.Model):
    _inherit = "website.page"

    is_portal_form = fields.Boolean(default=False)
