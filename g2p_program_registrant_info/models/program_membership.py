from odoo import api, fields, models


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    program_registrant_info_ids = fields.One2many(
        "g2p.program.registrant_info", "program_membership_id"
    )

    @api.constrains("partner_id", "program_id")
    def _onchange_program_registrant_info(self):
        old_prog_reg_infos = self.env["g2p.program.registrant_info"].search(
            [
                ("registrant_id", "=", self.partner_id.id),
                ("program_id", "=", self.program_id.id),
                ("program_membership_id", "!=", self.id),
            ]
        )
        old_prog_reg_infos.write({"program_membership_id": self.id})
