from odoo.tests import common


class TestG2PProgram(common.TransactionCase):
    def setUp(self):
        super(TestG2PProgram, self).setUp()
        self.Program = self.env["g2p.program"]
        self.StorageBackend = self.env["storage.backend"]

    def test_supporting_documents_store(self):
        # Create a test storage backend
        test_storage_backend = self.StorageBackend.create(
            {
                "name": "Test Storage Backend",
                # Add any other required fields
            }
        )

        # Create a test program
        test_program = self.Program.create(
            {
                "name": "Test Program",
                "supporting_documents_store": test_storage_backend.id,
                # Add any other required fields
            }
        )

        # Retrieve the supporting documents store for the program
        supporting_documents_store = test_program.supporting_documents_store

        # Assert that the supporting documents store is correct
        self.assertEqual(supporting_documents_store, test_storage_backend)
