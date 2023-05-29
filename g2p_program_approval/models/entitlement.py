from odoo import fields, models

from odoo.addons.g2p_programs.models import constants


class G2PApprovalEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    # The value of this will be taken from mapping
    approval_state = fields.Char()

    show_approve_button = fields.Boolean(compute="_compute_show_approve_button")

    def _compute_show_approve_button(self):
        for rec in self:
            ent_manager = rec.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
            rec.show_approve_button = ent_manager.show_approve_entitlements(rec)
