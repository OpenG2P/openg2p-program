from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestG2PEntitlementManagerDefault(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.entitlement_manager_model = cls.env["g2p.program.entitlement.manager.default"]
        cls.program_model = cls.env["g2p.program"]
        cls.cycle_model = cls.env["g2p.cycle"]

    def test_open_entitlements_form_regular_program(self):
        regular_program = self.program_model.create(
            {"name": "Regular Program", "is_reimbursement_program": False}
        )
        regular_cycle = self.cycle_model.create(
            {
                "name": "Regular Cycle",
                "program_id": regular_program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        action_regular = self.entitlement_manager_model.open_entitlements_form(regular_cycle)

        self.assertTrue(action_regular)
        self.assertNotIn("context", action_regular)

    def test_open_entitlements_form_reimbursement_program(self):
        reimbursement_program = self.program_model.create(
            {"name": "Reimbursement Program", "is_reimbursement_program": True}
        )
        reimbursement_cycle = self.cycle_model.create(
            {
                "name": "Reimbursement Cycle",
                "program_id": reimbursement_program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        action_reimbursement = self.entitlement_manager_model.open_entitlements_form(reimbursement_cycle)

        self.assertTrue(action_reimbursement)
        self.assertIn("context", action_reimbursement)
        self.assertEqual(
            action_reimbursement["context"].get("default_cycle_id"),
            reimbursement_cycle.id,
        )

    def test_open_entitlements_form_multiple_cycles(self):
        cycle1 = self.cycle_model.create(
            {
                "name": "Cycle 1",
                "program_id": self.program_model.create({"name": "Program 1"}).id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        cycle2 = self.cycle_model.create(
            {
                "name": "Cycle 2",
                "program_id": self.program_model.create({"name": "Program 2"}).id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        self.env.context = {"active_ids": [cycle1.id, cycle2.id]}

        action_multiple_cycles = self.entitlement_manager_model.open_entitlements_form(cycle=cycle1)

        self.assertTrue(action_multiple_cycles)

    def test_open_entitlements_form_reimbursement_program_action(self):
        reimbursement_program = self.program_model.create(
            {"name": "Reimbursement Program", "is_reimbursement_program": True}
        )
        reimbursement_cycle = self.cycle_model.create(
            {
                "name": "Reimbursement Cycle",
                "program_id": reimbursement_program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        action_reimbursement = self.entitlement_manager_model.open_entitlements_form(reimbursement_cycle)

        self.assertTrue(action_reimbursement)
        self.assertIn("context", action_reimbursement)
        self.assertEqual(
            action_reimbursement["context"].get("default_cycle_id"),
            reimbursement_cycle.id,
        )
        self.assertEqual(action_reimbursement["res_model"], "g2p.program.reimbursement")

    def test_open_entitlements_form_regular_program_action(self):
        regular_program = self.program_model.create(
            {"name": "Regular Program", "is_reimbursement_program": False}
        )
        regular_cycle = self.cycle_model.create(
            {
                "name": "Regular Cycle",
                "program_id": regular_program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        action_regular = self.entitlement_manager_model.open_entitlements_form(regular_cycle)

        self.assertTrue(action_regular)
        self.assertNotIn("context", action_regular)
        self.assertEqual(action_regular["res_model"], "g2p.program.entitlement")
