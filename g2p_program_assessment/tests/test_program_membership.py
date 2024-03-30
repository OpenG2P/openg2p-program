from logging import getLogger

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PProgramMembership(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.program = cls.env["g2p.program"].create({"name": "Test Program"})
        cls.membership = cls.env["g2p.program_membership"].create(
            {
                "partner_id": cls.partner.id,
                "program_id": cls.program.id,
                "state": "enrolled",
            }
        )

    def test_compute_show_prepare_assessment(self):
        self.membership._compute_show_prepare_assessment()
        self.assertTrue(self.membership.show_prepare_assessment_button)

        with self.assertLogs(getLogger(__name__), level="WARNING") as log:
            self.membership._compute_show_prepare_assessment()
            self.assertTrue(self.membership.show_prepare_assessment_button)
            self.assertIn("Program Registrant info not installed", log.output[0])

    def test_compute_show_create_entitlement(self):
        self.membership._compute_show_create_entitlement()

    def test_reject_application_assessment(self):
        with self.assertLogs("your_logger_name", level="WARNING") as log:
            self.assertFalse(self.membership.show_reject_application_assessment_button)

            result = self.membership.reject_application_assessment()

            self.assertEqual(result["type"], "ir.actions.client")
            self.assertEqual(result["tag"], "display_notification")
            self.assertEqual(result["params"]["title"], "Reject")
            self.assertEqual(result["params"]["message"], "No Application found.")
            self.assertEqual(result["params"]["type"], "warning")
            self.assertEqual(result["params"]["sticky"], False)

            self.assertIn("During reject: Program Registrant Info is not installed", log.output[0])
