from odoo import api, fields, models


class G2PProgramMembership(models.Model):
    _inherit = "g2p.program_membership"

    program_registrant_info_ids = fields.One2many(
        "g2p.program.registrant_info", "program_membership_id"
    )

    latest_registrant_info = fields.Many2one(
        "g2p.program.registrant_info", compute="_compute_latest_registrant_info"
    )
    latest_registrant_info_status = fields.Selection(
        related="latest_registrant_info.state"
    )

    def _compute_latest_registrant_info(self):
        for rec in self:
            latest_registrant_info = rec.program_registrant_info_ids.sorted(
                "create_date", reverse=True
            )
            if latest_registrant_info:
                rec.latest_registrant_info = latest_registrant_info[0]
            else:
                rec.latest_registrant_info = None

    @api.constrains("partner_id", "program_id")
    def _onchange_program_registrant_info(self):
        for rec in self:
            old_prog_reg_infos = self.env["g2p.program.registrant_info"].search(
                [
                    ("registrant_id", "=", rec.partner_id.id),
                    ("program_id", "=", rec.program_id.id),
                    ("program_membership_id", "!=", rec.id),
                ]
            )
            old_prog_reg_infos.write({"program_membership_id": rec.id})

    def create_program_registrant_info(self):
        self.ensure_one()
        return {
            "name": "Create Application",
            "type": "ir.actions.act_window",
            "res_model": "g2p.program.registrantinfo.wizard",
            "view_mode": "form",
            "target": "new",
        }
