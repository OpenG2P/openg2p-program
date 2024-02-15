from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestG2PPrograms(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.program_model = cls.env["g2p.program"]

    def test_open_eligible_beneficiaries_form(self):
        program_true = self.program_model.create(
            {"name": "Reimbursement Program", "is_reimbursement_program": True}
        )

        action_true = program_true.open_eligible_beneficiaries_form()

        self.assertEqual(action_true.get("name"), "Service Providers")

    def test_open_cycles_form(self):
        program_true = self.program_model.create(
            {"name": "Reimbursement Program", "is_reimbursement_program": True}
        )

        action_true = program_true.open_cycles_form()

        expected_views = [
            [self.env.ref("g2p_programs.view_cycle_tree").id, "tree"],
            [
                self.env.ref(
                    "g2p_program_reimbursement.view_cycle_reimbursement_form"
                ).id,
                "form",
            ],
        ]
        self.assertEqual(action_true.get("views"), expected_views)
