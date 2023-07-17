from odoo import _, fields, models

from odoo.addons.g2p_programs.models import constants


class G2PPrograms(models.Model):
    _inherit = "g2p.program"

    is_cycleless = fields.Boolean(default=False)

    default_active_cycle = fields.Many2one(
        "g2p.cycle", compute="_compute_default_active_cycle"
    )

    entitlements_count = fields.Integer(
        related="default_active_cycle.entitlements_count"
    )

    show_entitlement_field_name = fields.Char(compute="_compute_show_cycleless_fields")
    show_prepare_payments_button = fields.Boolean(
        compute="_compute_show_cycleless_fields"
    )
    show_send_payments_button = fields.Boolean(compute="_compute_show_cycleless_fields")

    def _compute_default_active_cycle(self):
        for rec in self:
            cycle_set = rec.cycle_ids.filtered_domain(
                [("state", "in", ["draft", "to_approve", "approved"])]
            ).sorted("start_date", reverse=True)
            rec.default_active_cycle = cycle_set[0] if len(cycle_set) > 0 else None

    def _compute_show_cycleless_fields(
        self, managers_for_payment_prepare=None, managers_for_payment_send=None
    ):
        for rec in self:
            program_dict = rec.read()[0]
            if program_dict.get("is_reimbursement_program", False):
                rec.show_entitlement_field_name = _("Reimbursements")
            else:
                rec.show_entitlement_field_name = _("Entitlements")

            rec.show_prepare_payments_button = False
            rec.show_send_payments_button = False

            accepted_payment_managers_for_prepare = [
                "g2p.program.payment.manager.phee",
                "g2p.program.payment.manager.interop.layer",
                "g2p.program.payment.manager.file",
                # "g2p.program.payment.manager.cash", # Is this required here?
            ]
            accepted_payment_managers_for_send = [
                "g2p.program.payment.manager.phee",
                "g2p.program.payment.manager.interop.layer",
                # "g2p.program.payment.manager.file", # there is not send in this case
                # "g2p.program.payment.manager.cash", # Is this required here?
            ]
            if managers_for_payment_prepare:
                accepted_payment_managers_for_prepare += managers_for_payment_prepare
            if managers_for_payment_send:
                accepted_payment_managers_for_send += managers_for_payment_send
            payment_manager = rec.get_manager(constants.MANAGER_PAYMENT)
            if (
                program_dict["is_cycleless"]
                and program_dict["state"] == "active"
                and payment_manager
            ):
                if payment_manager._name in accepted_payment_managers_for_prepare:
                    rec.show_prepare_payments_button = True
                if payment_manager._name in accepted_payment_managers_for_send:
                    rec.show_send_payments_button = True

    def open_entitlements_form(self):
        return self.default_active_cycle.open_entitlements_form()

    def prepare_payments_cycleless(self):
        return self.default_active_cycle.prepare_payment()

    def send_payments_cycleless(self):
        return self.default_active_cycle.send_payment()
