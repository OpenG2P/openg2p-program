from odoo.tests import common


class TestG2PProgramMembership(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.ProgramMembership = self.env["g2p.program_membership"]
        self.StorageFile = self.env["storage.file"]
        self.g2p_program = self.env["g2p.program"].create(
            {
                "name": "Test Program",
                # Add any other required fields
            }
        )

    def test_supporting_documents_ids(self):
        # Create a test program membership
        test_program_membership = self.ProgramMembership.create(
            {
                "name": "Test Program Membership",
                "program_id": self.g2p_program.id,
                # Add any other required fields
            }
        )

        # Create test supporting documents
        test_document_1 = self.StorageFile.create(
            {
                "name": "Test Document 1",
                "program_membership_id": test_program_membership.id,
                "backend_id": 1,
                # Add any other required fields
            }
        )

        test_document_2 = self.StorageFile.create(
            {
                "name": "Test Document 2",
                "program_membership_id": test_program_membership.id,
                "backend_id": 1,
                # Add any other required fields
            }
        )

        # Retrieve the supporting documents for the program membership
        supporting_documents = test_program_membership.supporting_documents_ids

        # Assert that the supporting documents are correct
        self.assertEqual(len(supporting_documents), 2)
        self.assertIn(test_document_1, supporting_documents)
        self.assertIn(test_document_2, supporting_documents)
