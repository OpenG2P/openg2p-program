from datetime import datetime, timedelta

from odoo.tests import common


class TestG2PEntitlement(common.TransactionCase):
    def setUp(self):
        super(TestG2PEntitlement, self).setUp()
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.g2p_program_membership = self.env["g2p.program_membership"].create(
            {
                "name": "Test Membership",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
            }
        )
        self.cycle = self.env["g2p.cycle"].create(
            {
                "name": "Test Cycle",
                "program_id": self.program.id,
                "sequence": 1,
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            }
        )

        self.entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
            }
        )

    def test_one_to_many_relationship(self):
        entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
            }
        )
        document1 = self.env["storage.file"].create(
            {"name": "Document 1", "entitlement_id": entitlement.id, "backend_id": 1}
        )
        document2 = self.env["storage.file"].create(
            {"name": "Document 2", "entitlement_id": entitlement.id, "backend_id": 1}
        )

        self.assertEqual(entitlement.supporting_document_ids, document1 + document2)
        self.assertEqual(document1.entitlement_id, entitlement)
        self.assertEqual(document2.entitlement_id, entitlement)

        # Remove a document and verify the relationship and count update
        document2.unlink()
        self.assertEqual(entitlement.supporting_document_ids, document1)
        self.assertEqual(entitlement.document_count, 1)

    def test_computed_field(self):
        """Verify that the computed field 'document_count' is calculated correctly."""
        entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
            }
        )
        self.assertEqual(entitlement.document_count, 0)

        # Create multiple documents and check the count
        documents = self.env["storage.file"].create(
            [
                {
                    "name": "Document {}".format(i),
                    "entitlement_id": entitlement.id,
                    "backend_id": 1,
                }
                for i in range(5)
            ]
        )
        self.assertEqual(entitlement.document_count, 5)

    def test_computed_field_dependency(self):
        """Ensure that the computed field is correctly invalidated when its dependencies change."""
        entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
            }
        )
        self.assertEqual(entitlement.document_count, 0)

        # Create a document and check the count
        self.env["storage.file"].create(
            {"name": "Document 1", "entitlement_id": entitlement.id, "backend_id": 1}
        )
        self.assertEqual(entitlement.document_count, 1)

        # Modify a non-related field and check that the count remains unchanged
        entitlement.write({"name": "Updated Entitlement"})
        self.assertEqual(entitlement.document_count, 1)

    def test_entitlement_copy_documents(self):
        # Create a program, partner, membership, and entitlement
        program = self.env["g2p.program"].create({"name": "Test Program"})
        partner = self.env["res.partner"].create({"name": "Test Beneficiary"})
        membership = self.env["g2p.program_membership"].create(
            {
                "program_id": program.id,
                "partner_id": partner.id,
            }
        )
        entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
            }
        )

        # Create supporting documents
        documents = self.env["storage.file"].create(
            [
                {
                    "name": "Document 1",
                    "program_membership_id": membership.id,
                    "backend_id": 1,
                },
                {
                    "name": "Document 2",
                    "program_membership_id": membership.id,
                    "backend_id": 1,
                },
            ]
        )

        # Call the method to copy documents
        entitlement.copy_documents_from_beneficiary()

        # Fetch updated entitlement record
        entitlement = self.env["g2p.entitlement"].browse(entitlement.id)

        # Assert that the documents are not linked to previous entitlements
        other_entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
            }
        )
        self.assertFalse(other_entitlement.supporting_document_ids)
        self.assertEqual(other_entitlement.document_count, 0)
