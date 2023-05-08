from odoo import models


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    def open_entitlement_form_wizard(self):

        return {
            "name": "Create Entitlement",
            "type": "ir.actions.act_window",
            "res_model": "g2p.entitlement.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "g2p_program_cycleless.view_create_entitlement_wizard_form"
            ).id,
            "target": "new",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_program_id": self.program_id.id,
                "default_currency_id": self.program_id.journal_id.currency_id.id,
                "default_cycle_id": self.program_id.default_active_cycle.id,
                "default_is_cash_entitlement": True,
            },
        }
