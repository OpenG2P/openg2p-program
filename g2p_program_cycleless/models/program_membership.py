from odoo import _, models


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    def create_entitlement(self):
        wizard = self.env["g2p.entitlement.wizard"].create(
            {
                "partner_id": self.partner_id.id,
                "program_id": self.program_id.id,
                "currency_id": self.program_id.journal_id.currency_id.id,
            }
        )

        return {
            "name": _("Create Entitlement"),
            "type": "ir.actions.act_window",
            "res_model": "g2p.entitlement.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }
