from werkzeug.exceptions import Forbidden

from odoo import api, fields, models


class ProgramApprovalMapping(models.Model):
    _name = "g2p.program.approval.mapping"
    _description = "Approval Mapping"
    _order = "sequence,id"

    sequence = fields.Integer(default=0)

    state = fields.Char(default="draft")

    group_id = fields.Many2one("res.groups")

    entitlement_manager_ref = fields.Char()

    _sql_constraints = [
        (
            "approval_stage_manager_unique",
            "unique (state, entitlement_manager_ref)",
            "Stage name must be unique per each manager.",
        ),
    ]

    @api.model
    def create(self, vals):
        if vals and not isinstance(vals, list):
            vals = [
                vals,
            ]
        for val in vals:
            val["sequence"] = val.get(
                "sequence", self.env["ir.sequence"].next_by_code("g2p.program.approval")
            )
        return super().create(vals)

    def get_next_mapping(self, state, raise_incorrect_user_error=True):
        success = False
        res = None
        if not len(self):
            success = True
            res = None
            return success, res
        if not state:
            state = self[0].state
        for rec in self:
            if success:
                res = rec
                break
            if rec.state == state:
                if raise_incorrect_user_error and rec.group_id.id not in self.env.user.groups_id.ids:
                    raise Forbidden()
                success = True
        return success, res
