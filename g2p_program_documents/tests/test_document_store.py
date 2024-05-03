from odoo.tests.common import TransactionCase


class TestG2PDocumentStore(TransactionCase):
    def setUp(self):
        super().setUp()
        self.G2PDocumentStore = self.env["storage.backend"]
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.g2p_program_membership = self.env["g2p.program_membership"].create(
            {
                "name": "Test Membership",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
            }
        )
        self.g2p_document_store = self.G2PDocumentStore.create(
            {
                "name": "Test Document Store",
                # Add any other required fields
            }
        )
        # Create a G2PDocumentStore instance
        document_store = self.env["storage.backend"].create(
            {
                "name": "Test Document Store",
                # ... other required fields ...
            }
        )
        # Call add_file with a program_membership
        file = document_store.add_file(
            data=b"Some test data",
            name="Test File",
            extension="txt",
        )
        # Assert that the program_membership_id is set
        self.assertEqual(file.program_membership_id, self.g2p_program_membership)

    def test_add_file_calls_super_method(self):
        """Test that add_file calls the superclass method correctly."""
        with self.mock_with_context(self.env["storage.backend"]._patch_method("add_file")) as mock_add_file:
            document_store = self.env["storage.backend"].create(
                {
                    "name": "Test Document Store",
                }
            )
            document_store.add_file(
                data=b"Some test data",
                name="Test File",
                extension="txt",
            )
            mock_add_file.assert_called_once_with(
                data=b"Some test data",
                name="Test File",
                extension="txt",
            )
