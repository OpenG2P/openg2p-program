from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestG2PEntitlementManagerDefault(TransactionCase):
    def setUp(self):
        super(TestG2PEntitlementManagerDefault, self).setUp()
        self.entitlement_manager = self.env["g2p.program.entitlement.manager.default"]
        self.program_model = self.env["g2p.program"]
        self.cycle_model = self.env["g2p.cycle"]

    def test_open_entitlements_form_reimbursement(self):
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

        action_reimbursement = self.entitlement_manager.open_entitlements_form(
            reimbursement_cycle
        )

        self.assertNotEqual(action_reimbursement["name"], "Reimbursements")
        self.assertNotEqual(action_reimbursement["name"], "Entitlements")

    def test_open_entitlements_form_cycleless(self):
        program = self.program_model.create(
            {
                "name": "Cycleless Program",
                "is_cycleless": True,
            }
        )

        cycle = self.cycle_model.create(
            {
                "name": "Test Cycle",
                "program_id": program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        manager = self.entitlement_manager.create(
            {
                "program_id": program.id,
                "name": "Test Manager",
            }
        )

        result = manager.open_entitlements_form(cycle)

        self.assertEqual(result["name"], "Entitlements")

    def test_open_entitlements_form_default(self):
        program = self.program_model.create(
            {
                "name": "Regular Program",
            }
        )

        cycle = self.cycle_model.create(
            {
                "name": "Test Cycle",
                "program_id": program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )

        manager = self.entitlement_manager.create(
            {
                "program_id": program.id,
                "name": "Test Manager",
            }
        )

        result = manager.open_entitlements_form(cycle)

        # Add assertions for the default behavior, if any
        self.assertNotEqual(result["name"], "Reimbursements")
        self.assertNotEqual(result["name"], "Entitlements")
