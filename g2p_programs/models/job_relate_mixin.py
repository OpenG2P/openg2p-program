from odoo import _, models
from odoo.exceptions import ValidationError


class JobRelateMixin(models.AbstractModel):
    _name = "job.relate.mixin"
    _description = "Job Relate Mixin"

    def action_view_related_queue_jobs(self):
        """Create an action for opening a related queue jobs in form view
        Usage:
            - Create/ Inherit a model which can be delay when a function is
            called.

            - Set inherit to this model
            ```python
            _inherit = ["job.relate.mixin", ...]
            ```
            - Create a button to call this method

        Returns:
            _type_: dict
        """
        self.ensure_one()
        if not self.user_has_groups("queue_job.group_queue_job_manager"):
            raise ValidationError(_("Only Queue Job Manager can do this action!"))
        jobs = self.env["queue.job"].sudo().search([("model_name", "=", self._name)])
        related_jobs = jobs.filtered(lambda qj: self in qj.records)
        action = self.env.ref("queue_job.action_queue_job").read()[0]
        action["domain"] = [("id", "in", related_jobs.ids)]
        return action
