from odoo import fields, models


class G2PPrograms(models.Model):
    _inherit = "g2p.program"

    is_cycleless = fields.Boolean(default=False)

    default_active_cycle = fields.Many2one(
        "g2p.cycle", compute="_compute_default_active_cycle"
    )

    entitlements_count = fields.Integer(
        related="default_active_cycle.entitlements_count"
    )

    def _compute_default_active_cycle(self):
        for rec in self:
            cycle_set = rec.cycle_ids.filtered_domain(
                [("state", "in", ["draft", "to_approve", "approved"])]
            ).sorted("start_date", reverse=True)
            rec.default_active_cycle = cycle_set[0] if len(cycle_set) > 0 else None

    def open_entitlements_form(self):
        return self.default_active_cycle.open_entitlements_form()

    def prepare_payments_cycleless(self):
        return self.default_active_cycle.prepare_payment()

    def send_payments_cycleless(self):
        return self.default_active_cycle.send_payment()
