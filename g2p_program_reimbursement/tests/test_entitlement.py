from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestG2PEntitlement(TransactionCase):
    def setUp(self):
        super().setUp()

        self.entitlement_model = self.env["g2p.entitlement"]
        self.partner_model = self.env["res.partner"]
        self.program_model = self.env["g2p.program"]
        self.file_model = self.env["ir.attachment"]
        self.cycle_model = self.env["g2p.cycle"]

        # Create a partner
        self.partner = self.partner_model.create(
            {
                "name": "Test Partner",
            }
        )

        # Create a program
        self.program = self.program_model.create(
            {
                "name": "Test Program",
                "is_reimbursement_program": False,
            }
        )

        # Create a cycle
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        self.cycle = self.cycle_model.create(
            {
                "name": "Test Cycle",
                "program_id": self.program.id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )

        # Create an entitlement with a valid partner_id
        self.entitlement = self.entitlement_model.create(
            {
                "program_id": self.program.id,
                "partner_id": self.partner.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 1000.0,
                "is_cash_entitlement": True,
                "state": "draft",
            }
        )

        # Create a supporting document file
        self.supporting_document_file = self.file_model.create(
            {
                "name": "Test Document",
                "datas": "Test Data",
            }
        )

    def test_compute_name(self):
        self.entitlement._compute_name()
        self.assertEqual(
            self.entitlement.name,
            "Entitlement Cash [False 1,000.00]",
            "Compute Name failed for cash entitlement.",
        )

    # def test_submit_reimbursement_claim(self):
    #     claim_code = self.entitlement.code
    #     result_code, reimbursement = self.entitlement.submit_reimbursement_claim(
    #         partner=self.partner,
    #         received_code=claim_code,
    #         supporting_document_file_ids=[self.supporting_document_file.id],
    #         amount=1200.0,
    #         transfer_fee=50.0,
    #     )

    #     self.assertEqual(
    #         result_code,
    #         0,
    #         "Submit Reimbursement Claim failed with code {}.".format(result_code)
    #     )

    #     self.assertTrue(
    #         reimbursement,
    #         "Reimbursement creation failed."
    #     )

    #     self.assertEqual(
    #         reimbursement.initial_amount,
    #         1200.0,
    #         "Reimbursement amount mismatch."
    #     )

    #     self.assertEqual(
    #         reimbursement.transfer_fee,
    #         50.0,
    #         "Reimbursement transfer fee mismatch."
    #     )

    def test_submit_reimbursement_claim_wrong_code(self):
        wrong_claim_code = "wrong_code"
        result_code, reimbursement = self.entitlement.submit_reimbursement_claim(
            partner=self.partner,
            received_code=wrong_claim_code,
            supporting_document_file_ids=[self.supporting_document_file.id],
            amount=1200.0,
            transfer_fee=50.0,
        )

        self.assertEqual(
            result_code,
            2,
            f"Submit Reimbursement Claim succeeded with wrong code {wrong_claim_code}.",
        )

        self.assertFalse(reimbursement, "Reimbursement should not be created with wrong code.")
