import logging

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class DefaultCycleManagerInherited(models.Model):
    _inherit = "g2p.cycle.manager.default"

    eligibility_domain = fields.Text(string="Domain", default="[]")
    inclusion_limit = fields.Integer(default=0)

    sorting_criteria_ids = fields.One2many("g2p.sorting.criteria", "manager_id", string="Sorting Order")

    @api.model
    def create(self, vals):
        if "program_id" in vals:
            vals[
                "eligibility_domain"
            ] = f"[('program_membership_ids.program_id', 'in', [{vals['program_id']}])]"
        return super().create(vals)

    def new_cycle(self, name, new_start_date, sequence):
        cycle = super().new_cycle(name, new_start_date, sequence)

        for rec in self:
            is_disbursement = (
                self.program_id.program_managers.manager_ref_id.is_disbursement_through_priority_list
            )
            if is_disbursement:
                for sorting_criterion in self.sorting_criteria_ids:
                    self.env["g2p.sorting.criteria"].create(
                        {
                            "cycle_id": cycle.id,
                            "sequence": sorting_criterion.sequence,
                            "field_name": sorting_criterion.field_name.id,
                            "order": sorting_criterion.order,
                        }
                    )

                cycle.write(
                    {"inclusion_limit": rec.inclusion_limit, "eligibility_domain": rec.eligibility_domain}
                )
        return cycle

    def add_beneficiaries(self, cycle, beneficiaries, state="draft"):
        self.ensure_one()
        self._ensure_can_edit_cycle(cycle)
        _logger.debug("Adding beneficiaries to the cycle %s", cycle.name)
        _logger.debug("Beneficiaries: %s", len(beneficiaries))

        # Only add beneficiaries not added yet
        existing_ids = cycle.cycle_membership_ids.mapped("partner_id.id")
        _logger.debug("Existing IDs: %s", len(existing_ids))
        beneficiaries = list(set(beneficiaries) - set(existing_ids))

        is_disbursement = (
            self.program_id.program_managers.manager_ref_id.is_disbursement_through_priority_list
        )
        if is_disbursement:
            # Convert beneficiaries to recordset first
            if beneficiaries:
                if isinstance(beneficiaries, list):
                    ids = beneficiaries
                else:
                    ids = beneficiaries.mapped("partner_id.id")

            domain = safe_eval(cycle.eligibility_domain)

            domain += [("id", "in", ids), ("disabled", "=", False)]
            if self.program_id.target_type == "group":
                domain += [("is_group", "=", True), ("is_registrant", "=", True)]
            if self.program_id.target_type == "individual":
                domain += [("is_group", "=", False), ("is_registrant", "=", True)]

            remaining_limit = max(0, cycle.inclusion_limit - len(existing_ids))

            sorted_criteria = cycle.sorting_criteria_ids.sorted("sequence")

            order = []
            for criterion in sorted_criteria:
                field_name = criterion.field_name.name
                reverse_flag = criterion.order == "desc"
                order_direction = "desc" if reverse_flag else "asc"
                order.append(f"{field_name} {order_direction}")

            # Join the order list into a comma-separated string
            order_str = ",".join(order)

            # Query partners with sorting applied
            sorted_beneficiaries = self.env["res.partner"].search(domain, order=order_str)

            if len(sorted_beneficiaries) > remaining_limit:
                beneficiaries = sorted_beneficiaries[:remaining_limit].ids
            else:
                beneficiaries = sorted_beneficiaries.ids

        if len(beneficiaries) == 0:
            message = _("No beneficiaries to import.")
            kind = "warning"
            sticky = False
        elif len(beneficiaries) < self.MIN_ROW_JOB_QUEUE:
            self._add_beneficiaries(cycle, beneficiaries, state, do_count=True)
            message = _("%s beneficiaries imported.", len(beneficiaries))
            kind = "success"
            sticky = False
        else:
            self._add_beneficiaries_async(cycle, beneficiaries, state)
            message = _("Import of %s beneficiaries started.", len(beneficiaries))
            kind = "warning"
            sticky = True

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Enrollment"),
                "message": message,
                "sticky": sticky,
                "type": kind,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }

    def _add_beneficiaries(self, cycle, beneficiaries, state="draft", do_count=False):
        """Add Beneficiaries with Rank

        :param cycle: Recordset of cycle
        :param beneficiaries: Recordset of beneficiaries
        :param state: String state to be set to beneficiary
        :return: None
        """
        new_beneficiaries = []
        for index, r in enumerate(beneficiaries):
            new_beneficiaries.append(
                [
                    0,
                    0,
                    {
                        "partner_id": r,
                        "enrollment_date": fields.Date.today(),
                        "state": state,
                        "rank": index + 1,
                    },
                ]
            )
        cycle.update({"cycle_membership_ids": new_beneficiaries})
        cycle._compute_members_count()
