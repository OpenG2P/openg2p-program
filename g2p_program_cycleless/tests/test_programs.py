from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import _
from odoo.tests import common


class TestG2PPrograms(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a cycle-based and a cycleless program
        self.cycle_based_program = self.env["g2p.program"].create({"name": "Cycle-Based Program"})
        self.cycleless_program = self.env["g2p.program"].create(
            {"name": "Cycleless Program", "is_cycleless": True}
        )
        self.cycle_model = self.env["g2p.cycle"]
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.program = self.env["res.partner"].create({"name": "Test Program"})

    def test_default_active_cycle_cycle_based(self):
        # Create two cycles with different states
        cycle1 = self.cycle_based_program.cycle_ids.create(
            {
                "name": "Test Cycle1",
                "program_id": self.cycle_based_program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
                "state": "approved",
            }
        )
        cycle2 = self.cycle_based_program.cycle_ids.create(
            {
                "name": "Test Cycle2",
                "program_id": self.cycle_based_program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
                "state": "to_approve",
            }
        )

        # Assert that the most recently approved cycle is the default active cycle
        self.assertEqual(self.cycle_based_program.default_active_cycle, cycle1)
        self.assertNotEqual(self.cycle_based_program.default_active_cycle, cycle2)

    def test_compute_show_cycleless_fields(self):
        program_dict = {"is_reimbursement_program": False, "is_cycleless": True, "state": "active"}
        program = self.cycleless_program.create({"name": "Test Program"})

        # Patch the read method of the g2p.program model
        with patch("odoo.models.Model.read", return_value=[program_dict]):
            program._compute_show_cycleless_fields(
                managers_for_payment_prepare=["g2p.program.payment.manager.file"],
                managers_for_payment_send=["g2p.program.payment.manager.interop.layer"],
            )
        # Assert computed fields
        self.assertEqual(
            program.show_entitlement_field_name,
            _("Entitlements"),
            "Show entitlement field name should be 'Entitlements'",
        )

    def test_compute_show_cycleless_fields_reimburse(self):
        program_dict = {"is_reimbursement_program": True, "is_cycleless": True, "state": "active"}
        program = self.cycleless_program.create({"name": "Test Program"})

        # Patch the read method of the g2p.program model
        with patch("odoo.models.Model.read", return_value=[program_dict]):
            program._compute_show_cycleless_fields(
                managers_for_payment_prepare=["g2p.program.payment.manager.file"],
                managers_for_payment_send=["g2p.program.payment.manager.interop.layer"],
            )
        # Assert computed fields
        self.assertEqual(
            program.show_entitlement_field_name,
            _("Reimbursements"),
            "Show entitlement field name should be 'Reimbursements'",
        )

    def test_open_entitlements_form(self):
        program = self.cycle_based_program.create({"name": "Test Program"})
        # Create a cycle for the program
        cycle = self.cycle_model.create(
            {
                "name": "Test Cycle",
                "program_id": program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
            }
        )
        # Mock the behavior of open_entitlements_form method
        with patch.object(type(cycle), "open_entitlements_form", return_value="Entitlements form opened"):
            program.default_active_cycle = cycle

            result = program.open_entitlements_form()

            self.assertEqual(
                result,
                "Entitlements form opened",
                "Should return the result of default_active_cycle's open_entitlements_form method",
            )
