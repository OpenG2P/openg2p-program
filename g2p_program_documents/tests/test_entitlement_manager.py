from datetime import datetime, timedelta

from odoo.exceptions import UserError
from odoo.tests import common


class TestDefaultEntitlementManagerForDocument(common.TransactionCase):
    def setUp(self):
        super(TestDefaultEntitlementManagerForDocument, self).setUp()

        # Create program, partner, membership, and document
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.partner = self.env["res.partner"].create({"name": "Test Beneficiary"})
        self.membership = self.env["g2p.program_membership"].create(
            {
                "program_id": self.program.id,
                "partner_id": self.partner.id,
            }
        )
        self.document = self.env["storage.file"].create(
            {
                "name": "Test Document",
                "program_membership_id": self.membership.id,
                "backend_id": 1,
            }
        )

        # Create custom manager instance
        self.manager = self.env["g2p.program.entitlement.manager.default"].create(
            {
                "program_id": self.program.id,
                "name": "Test Manager",
            }
        )

    def test_entitlement_copy_documents(self):
        # Create cycle and beneficiaries
        cycle = self.env["g2p.cycle"].create(
            {
                "name": "Test Cycle",
                "program_id": self.program.id,
                "sequence": 1,
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            }
        )
        beneficiaries = [self.partner.id]  # List of partner IDs

        # Call the method with custom manager
        ents = self.manager.prepare_entitlements(cycle, beneficiaries)

        # Assert that entitlements are created and documents are copied
        self.assertTrue(ents)
        for ent in ents:
            self.assertEqual(ent.supporting_document_ids, self.document)

    def test_entitlement_copy_documents_no_documents(self):
        # No documents linked to membership
        self.document.program_membership_id = False

        # Create cycle and beneficiaries
        cycle = self.env["g2p.cycle"].create(
            {
                "name": "Test Cycle",
                "program_id": self.program.id,
                "sequence": 1,
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            }
        )
        beneficiaries = [self.partner.id]

        # Call the method with custom manager (should not raise error)
        ents = self.manager.prepare_entitlements(cycle, beneficiaries)

        # Assert that entitlements are created without documents
        self.assertTrue(ents)
        for ent in ents:
            self.assertFalse(ent.supporting_document_ids)

    def test_entitlement_copy_documents_error(self):
        # Mock a method to raise an error during document copying
        def mock_copy_documents_from_beneficiary(self):
            raise UserError("Test Error")

        # Patch the method with the mock
        with self.env.patch.object(
            self.env["g2p.entitlement"],
            "copy_documents_from_beneficiary",
            mock_copy_documents_from_beneficiary,
        ):
            # Create cycle and beneficiaries
            cycle = self.env["g2p.cycle"].create(
                {
                    "name": "Test Cycle",
                    "program_id": self.program.id,
                    "sequence": 1,
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": (datetime.now() + timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )
            beneficiaries = [self.partner.id]

            # Call the method with custom manager (should raise UserError)
            with self.assertRaises(UserError):
                self.manager.prepare_entitlements(cycle, beneficiaries)
