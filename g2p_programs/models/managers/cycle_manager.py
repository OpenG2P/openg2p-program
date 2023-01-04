# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.queue_job.delay import group

from .. import constants

_logger = logging.getLogger(__name__)


class CycleManager(models.Model):
    _name = "g2p.cycle.manager"
    _description = "Cycle Manager"
    _inherit = "g2p.manager.mixin"

    program_id = fields.Many2one("g2p.program", "Program")

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = ("g2p.cycle.manager.default", "Default")
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class BaseCycleManager(models.AbstractModel):
    _name = "g2p.base.cycle.manager"
    _description = "Base Cycle Manager"

    name = fields.Char("Manager Name", required=True)
    program_id = fields.Many2one("g2p.program", string="Program", required=True)

    auto_approve_entitlements = fields.Boolean(
        string="Auto-approve Entitlements", default=False
    )

    def check_eligibility(self, cycle, beneficiaries=None):
        """
        Validate the eligibility of each beneficiary for the cycle
        """
        raise NotImplementedError()

    def prepare_entitlements(self, cycle):
        """
        Prepare the entitlements for the cycle
        """
        raise NotImplementedError()

    def issue_payments(self, cycle):
        """
        Issue the payments based on entitlements for the cycle
        """
        raise NotImplementedError()

    def validate_entitlements(self, cycle, cycle_memberships):
        """
        Validate the entitlements for the cycle
        """
        raise NotImplementedError()

    def new_cycle(self, name, new_start_date, sequence):
        """
        Create a new cycle for the program
        """
        raise NotImplementedError()

    def mark_distributed(self, cycle):
        """
        Mark the cycle as distributed
        """
        raise NotImplementedError()

    def mark_ended(self, cycle):
        """
        Mark the cycle as ended
        """
        raise NotImplementedError()

    def mark_cancelled(self, cycle):
        """
        Mark the cycle as cancelled
        """
        raise NotImplementedError()

    def add_beneficiaries(self, cycle, beneficiaries, state="draft"):
        """
        Add beneficiaries to the cycle
        """
        raise NotImplementedError()

    def on_start_date_change(self, cycle):
        """
        Hook for when the start date change
        """

    def on_state_change(self, cycle):
        """
        Hook for when the state change
        Args:
            cycle:

        Returns:

        """

    def _ensure_can_edit_cycle(self, cycle):
        """Base :meth:'_ensure_can_edit_cycle`
        Check if the cycle can be editted

        :param cycle: A recordset of cycle
        :return:
        """
        if cycle.state not in [cycle.STATE_DRAFT]:
            raise ValidationError(_("The Cycle is not in draft mode"))

    def mark_import_as_done(self, cycle, msg):
        """Base :meth:`mark_import_as_done`
        Post a message in the chatter

        :param cycle: A recordset of cycle
        :param msg: A string to be posted in the chatter
        :return:
        """
        self.ensure_one()
        cycle.locked = False
        cycle.locked_reason = None
        cycle.message_post(body=msg)


class DefaultCycleManager(models.Model):
    _name = "g2p.cycle.manager.default"
    _inherit = ["g2p.base.cycle.manager", "g2p.manager.source.mixin"]
    _description = "Default Cycle Manager"

    cycle_duration = fields.Integer(default=30, required=True)
    approver_group_id = fields.Many2one(
        comodel_name="res.groups",
        string="Approver Group",
        copy=True,
    )

    def check_eligibility(self, cycle, beneficiaries=None):
        """
        Default Cycle Manager eligibility checker

        :param cycle: The cycle that is being verified
        :type cycle: :class:`g2p_programs.models.cycle.G2PCycle`
        :param beneficiaries: the beneficiaries that need to be verified. By Default the one with the state ``draft``
                or ``enrolled`` are verified.
        :type beneficiaries: list or None

        :return: The list of eligible beneficiaries
        :rtype: list

        Validate the eligibility of each beneficiary for the cycle using the configured manager(s)
        :class:`g2p_programs.models.managers.eligibility_manager.BaseEligibilityManager`. If there is multiple managers
        for eligibility, each of them are run using the filtered list of eligible beneficiaries from the previous
        one.

        The ``state`` of beneficiaries is updated to either ``enrolled`` if they match the enrollment criteria
        or ``not_eligible`` in case they do not match them.


        """
        for rec in self:
            rec._ensure_can_edit_cycle(cycle)

            # Get all the draft and enrolled beneficiaries
            if beneficiaries is None:
                beneficiaries = cycle.get_beneficiaries(["draft", "enrolled"])

            eligibility_managers = rec.program_id.get_managers(
                constants.MANAGER_ELIGIBILITY
            )
            filtered_beneficiaries = beneficiaries
            for manager in eligibility_managers:
                filtered_beneficiaries = manager.verify_cycle_eligibility(
                    cycle, filtered_beneficiaries
                )

            filtered_beneficiaries.write({"state": "enrolled"})

            beneficiaries_ids = beneficiaries.ids
            filtered_beneficiaries_ids = filtered_beneficiaries.ids
            ids_to_remove = list(
                set(beneficiaries_ids) - set(filtered_beneficiaries_ids)
            )

            # Mark the beneficiaries as not eligible
            memberships_to_remove = self.env["g2p.cycle.membership"].browse(
                ids_to_remove
            )
            memberships_to_remove.write({"state": "not_eligible"})

            # Disable the entitlements of the beneficiaries
            entitlements = self.env["g2p.entitlement"].search(
                [
                    ("cycle_id", "=", cycle.id),
                    ("partner_id", "in", memberships_to_remove.mapped("partner_id.id")),
                ]
            )
            entitlements.write({"state": "cancelled"})

            return filtered_beneficiaries

    def prepare_entitlements(self, cycle):
        for rec in self:
            rec._ensure_can_edit_cycle(cycle)
            # Get all the enrolled beneficiaries
            beneficiaries_count = cycle.get_beneficiaries(["enrolled"], count=True)
            rec.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
            if beneficiaries_count < 200:
                self._prepare_entitlements(cycle)
            else:
                self._prepare_entitlements_async(cycle, beneficiaries_count)

    def _prepare_entitlements_async(self, cycle, beneficiaries_count):
        _logger.debug("Prepare entitlement asynchronously")
        cycle.message_post(
            body=_(
                "Prepare entitlement for %s beneficiaries started.", beneficiaries_count
            )
        )
        cycle.write(
            {
                "locked": True,
                "locked_reason": _("Prepare entitlement for beneficiaries."),
            }
        )

        jobs = []
        for i in range(0, beneficiaries_count, 2000):
            jobs.append(self.delayable()._prepare_entitlements(cycle, i, 2000))
        main_job = group(*jobs)
        main_job.on_done(
            self.delayable().mark_import_as_done(cycle, _("Entitlement Ready."))
        )
        main_job.delay()

    def _prepare_entitlements(self, cycle, offset=0, limit=None):
        beneficiaries = cycle.get_beneficiaries(
            ["enrolled"], offset=offset, limit=limit, order="id"
        )
        entitlement_manager = self.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
        entitlement_manager.prepare_entitlements(cycle, beneficiaries)

    def mark_distributed(self, cycle):
        cycle.update({"state": constants.STATE_DISTRIBUTED})

    def mark_ended(self, cycle):
        cycle.update({"state": constants.STATE_ENDED})

    def mark_cancelled(self, cycle):
        cycle.update({"state": constants.STATE_CANCELLED})

    def validate_entitlements(self, cycle, entitlement_ids):
        # TODO: call the program's entitlement manager and validate the entitlements
        # TODO: Use a Job attached to the cycle
        # TODO: Implement validation workflow
        for rec in self:
            rec._ensure_can_edit_cycle(cycle)
            rec.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
            if len(entitlement_ids) < 200:
                self._validate_entitlements(entitlement_ids)
            else:
                self._validate_entitlements_async(cycle, entitlement_ids)

    def _validate_entitlements_async(self, cycle, entitlement_ids):
        _logger.debug("Validate entitlement asynchronously")
        cycle.message_post(
            body=_("Validation for %s entitlements started.", len(entitlement_ids))
        )
        cycle.write(
            {
                "locked": True,
                "locked_reason": _("Validate entitlement for beneficiaries."),
            }
        )

        jobs = []
        max_jobs_per_batch = 100
        entitlements = []
        max_rec = len(entitlement_ids)
        for ctr_entitlements, entitlement in enumerate(entitlement_ids, 1):
            entitlements.append(entitlement.id)
            if (
                ctr_entitlements % max_jobs_per_batch == 0
            ) or ctr_entitlements == max_rec:
                entitlements_ids = self.env["g2p.entitlement"].search(
                    [("id", "in", entitlements)]
                )
                jobs.append(self.delayable()._validate_entitlements(entitlements_ids))
                entitlements = []

        main_job = group(*jobs)
        main_job.on_done(
            self.delayable().mark_import_as_done(cycle, _("Entitlement approved."))
        )
        main_job.delay()

    def _validate_entitlements(self, entitlements):
        entitlement_manager = self.program_id.get_manager(constants.MANAGER_ENTITLEMENT)
        entitlement_manager.approve_entitlements(entitlements)

    def new_cycle(self, name, new_start_date, sequence):
        _logger.info("Creating new cycle for program %s", self.program_id.name)
        _logger.info("New start date: %s", new_start_date)
        for rec in self:
            cycle = self.env["g2p.cycle"].create(
                {
                    "program_id": rec.program_id.id,
                    "name": name,
                    "state": "draft",
                    "sequence": sequence,
                    "start_date": new_start_date,
                    "end_date": new_start_date + timedelta(days=rec.cycle_duration),
                }
            )
            _logger.info("New cycle created: %s", cycle.name)
            return cycle

    def copy_beneficiaries_from_program(self, cycle, state="enrolled"):
        self._ensure_can_edit_cycle(cycle)
        self.ensure_one()

        for rec in self:
            beneficiary_ids = rec.program_id.get_beneficiaries(["enrolled"]).mapped(
                "partner_id.id"
            )
            return rec.add_beneficiaries(cycle, beneficiary_ids, state)

    def add_beneficiaries(self, cycle, beneficiaries, state="draft"):
        """
        Add beneficiaries to the cycle
        """
        self.ensure_one()
        self._ensure_can_edit_cycle(cycle)
        _logger.info("Adding beneficiaries to the cycle %s", cycle.name)
        _logger.info("Beneficiaries: %s", beneficiaries)

        # Only add beneficiaries not added yet
        existing_ids = cycle.cycle_membership_ids.mapped("partner_id.id")
        beneficiaries = list(set(beneficiaries) - set(existing_ids))
        if len(beneficiaries) == 0:
            message = _("No beneficiaries to import.")
            kind = "warning"
        elif len(beneficiaries) < 1000:
            self._add_beneficiaries(cycle, beneficiaries, state)
            message = _("%s beneficiaries imported.", len(beneficiaries))
            kind = "success"
        else:
            self._add_beneficiaries_async(cycle, beneficiaries, state)
            message = _("Import of %s beneficiaries started.", len(beneficiaries))
            kind = "warning"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Enrollment"),
                "message": message,
                "sticky": True,
                "type": kind,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }

    def _add_beneficiaries_async(self, cycle, beneficiaries, state):
        _logger.info("Adding beneficiaries asynchronously")
        cycle.message_post(
            body="Import of %s beneficiaries started." % len(beneficiaries)
        )
        cycle.write({"locked": True, "locked_reason": _("Importing beneficiaries.")})

        jobs = []
        for i in range(0, len(beneficiaries), 2000):
            jobs.append(
                self.delayable()._add_beneficiaries(
                    cycle, beneficiaries[i : i + 2000], state
                )
            )
        main_job = group(*jobs)
        main_job.on_done(
            self.delayable().mark_import_as_done(
                cycle, _("Beneficiary import finished.")
            )
        )
        main_job.delay()

    def _add_beneficiaries(self, cycle, beneficiaries, state="draft"):
        new_beneficiaries = []
        for r in beneficiaries:
            new_beneficiaries.append(
                [
                    0,
                    0,
                    {
                        "partner_id": r,
                        "enrollment_date": fields.Date.today(),
                        "state": state,
                    },
                ]
            )
        cycle.update({"cycle_membership_ids": new_beneficiaries})

    def on_state_change(self, cycle):
        if cycle.state == cycle.STATE_APPROVED:
            if not self.approver_group_id:
                raise ValidationError(_("The cycle approver group is not specified!"))
            else:
                if (
                    self.env.user.id != 1
                    and self.env.user.id not in self.approver_group_id.users.ids
                ):
                    raise ValidationError(
                        _("You are not allowed to approve this cycle!")
                    )
