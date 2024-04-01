from datetime import datetime, timedelta

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestG2PDocument(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create necessary records or perform any setup needed for the tests
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

        self.g2p_entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
            }
        )

        self.storage_file = self.env["storage.file"].create(
            {
                "name": "Test File",
                "program_membership_id": self.g2p_program_membership.id,
                "entitlement_id": self.g2p_entitlement.id,
                "backend_id": 1,
            }
        )

    def test_get_binary(self):
        # Ensure that get_binary method creates an attachment and returns the correct result
        self.storage_file.get_binary()

        # Check if the attachment is created
        self.assertTrue(self.storage_file.attachment_id)

        # Check if the attachment is associated with the correct file
        self.assertEqual(self.storage_file.attachment_id.res_id, self.storage_file.id)

        # Check if the attachment type is binary
        self.assertEqual(self.storage_file.attachment_id.type, "binary")

        # Check if the method returns a dictionary with expected keys
        binary_data = self.storage_file.get_binary()
        self.assertIsInstance(binary_data, dict)
        self.assertIn("id", binary_data)
        self.assertIn("mimetype", binary_data)
        self.assertIn("index_content", binary_data)
        self.assertIn("url", binary_data)

    def test_get_binary_no_attachment(self):
        # Ensure that get_binary method handles the case when no attachment is present
        self.storage_file.attachment_id = False

        # Check if the method creates an attachment when there is no attachment
        self.storage_file.get_binary()

        # Check if the attachment is created
        self.assertTrue(self.storage_file.attachment_id)

    def test_get_binary_no_permission(self):
        # Ensure that get_binary method raises AccessError when user has no permission
        # For example, you might check if the user has read access to the file
        with self.assertRaises(AccessError):
            self.env.user.write({"groups_id": [(3, self.ref("base.group_user"))]})
            self.storage_file.get_binary()
