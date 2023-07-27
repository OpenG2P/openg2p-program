# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class G2PAssignToProgramWizard(models.TransientModel):
    _inherit = "g2p.assign.program.wizard"

    program_id = fields.Many2one(
        "g2p.program",
        "",
        domain="[('target_type', '=', target_type),('is_reimbursement_program', '=', False), ('state', '=', 'active')]",
        help="A program",
        required=True,
    )

    def open_wizard(self):

        partner_id = self.env.context.get("active_ids")[0]
        partner = self.env["res.partner"].search(
            [
                ("id", "=", partner_id),
            ]
        )

        if partner.supplier_rank > 0:
            return {
                "name": "Add to Program",
                "view_mode": "form",
                "res_model": "g2p.assign.program.wizard",
                "view_id": self.env.ref(
                    "g2p_program_reimbursement.assign_service_provider_to_program_wizard_form_view"
                ).id,
                "type": "ir.actions.act_window",
                "target": "new",
                "context": self.env.context,
            }

        return super(G2PAssignToProgramWizard, self).open_wizard()
