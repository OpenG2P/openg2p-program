from datetime import datetime, timedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PCycle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestG2PCycle, cls).setUpClass()
        cls.cycle_model = cls.env["g2p.cycle"]
        cls.program_model = cls.env["g2p.program"]

    def test_01_is_reimbursement_program(self):
        program = self.program_model.create(
            {"name": "Reimbursement Program", "is_reimbursement_program": True}
        )

        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        cycle = self.cycle_model.create(
            {
                "name": "Test Cycle",
                "program_id": program.id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        self.assertTrue(cycle.is_reimbursement_program, "is_reimbursement_program should be True")

    def test_02_open_cycle_form(self):
        program = self.program_model.create(
            {"name": "Reimbursement Program", "is_reimbursement_program": True}
        )

        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        cycle = self.cycle_model.create(
            {
                "name": "Test Cycle",
                "program_id": program.id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )

        res = cycle.open_cycle_form()

        if program.is_reimbursement_program:
            expected_view_id = self.env.ref("g2p_program_reimbursement.view_cycle_reimbursement_form").id
            self.assertEqual(
                res["view_id"],
                expected_view_id,
                "View ID is not as expected for reimbursement programs",
            )
        else:
            self.assertIsNone(
                res.get("view_id"),
                "View ID should be None for non-reimbursement programs",
            )
