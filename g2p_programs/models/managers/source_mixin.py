# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import api, models


class ManagerSourceMixin(models.AbstractModel):
    """Manager Data Source mixin."""

    _name = "g2p.manager.source.mixin"
    _description = "Manager Data Source Mixin"

    @api.model
    def create(self, vals):
        """Override to update reference to source on the manager."""
        res = super().create(vals)
        # TODO: Seems not required but this causes error when called from the create program wizard.
        # Disable for now
        # if self.env.context.get("active_model"):
        #    # update reference on manager
        #    self.env[self.env.context["active_model"]].browse(
        #        self.env.context["active_id"]
        #    ).manager_id = res.id
        return res

    def unlink(self):
        for rec in self:
            program_id = rec.read()[0].get("program_id", None)
            if program_id:
                program_id = program_id[0]
                program = self.env["g2p.program"].browse(program_id)
                manager = self.get_manager_for_unlink(program, f"{rec._name},{rec.id}")
                if manager:
                    manager.unlink()
        return super().unlink()

    @api.model
    def get_manager_for_unlink(self, program_id, manager_ref):
        for manager in program_id.eligibility_managers:
            if manager_ref == manager.read()[0].get("manager_ref_id", ""):
                return manager
        for manager in program_id.deduplication_managers:
            if manager_ref == manager.read()[0].get("manager_ref_id", ""):
                return manager
        for manager in program_id.notification_managers:
            if manager_ref == manager.read()[0].get("manager_ref_id", ""):
                return manager
        for manager in program_id.program_managers:
            if manager_ref == manager.read()[0].get("manager_ref_id", ""):
                return manager
        for manager in program_id.cycle_managers:
            if manager_ref == manager.read()[0].get("manager_ref_id", ""):
                return manager
        for manager in program_id.entitlement_managers:
            if manager_ref == manager.read()[0].get("manager_ref_id", ""):
                return manager
        for manager in program_id.payment_managers:
            if manager_ref == manager.read()[0].get("manager_ref_id", ""):
                return manager
        return None

    def get_manager_view_id(self):
        """Retrieve form view."""
        return (
            self.env["ir.ui.view"]
            .search([("model", "=", self._name), ("type", "=", "form")], limit=1)
            .id
        )
