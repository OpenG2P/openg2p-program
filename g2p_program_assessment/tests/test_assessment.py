import logging
from datetime import datetime

from odoo import tools
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestG2PProgramAssessment(TransactionCase):
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
        cls.cycle = cls.env["g2p.cycle"].create(
            {
                "name": "Test Cycle",
                "program_id": cls.program.id,
                "start_date": datetime.now(),
                "end_date": datetime.now(),
            }
        )
        cls.entitlement = cls.env["g2p.entitlement"].create(
            {
                "partner_id": cls.partner.id,
                "program_id": cls.program.id,
                "cycle_id": cls.cycle.id,
                "initial_amount": 1000.0,
                "is_cash_entitlement": True,
                "state": "draft",
            }
        )

    def test_post_assessment(self):
        body = "This is a test assessment."
        res_model = "g2p.program_membership"
        res_id = self.membership.id

        assessments = self.env["g2p.program.assessment"].post_assessment(
            body,
            res_model,
            res_id,
            is_comment=False,
            subject="Test Subject",
            message_type="comment",
            subtype_id=None,
            partner_ids=None,
            # record_name="Test Record",
        )
        self.assertTrue(assessments)
        self.assertEqual(len(assessments), 1)
        assessment = assessments[0]
        self.assertEqual(assessment.name, "Test Subject")
        expected_body = "<p>This is a test assessment.</p>"
        self.assertEqual(tools.ustr(assessment.remarks_id.body), expected_body)
        self.assertEqual(assessment.is_comment, False)

    def test_get_res_field_name(self):
        res_model_membership = "g2p.program_membership"
        res_model_entitlement = "g2p.entitlement"
        res_model_other = "some.other.model"

        field_name_membership = self.env["g2p.program.assessment"].get_res_field_name(res_model_membership)
        field_name_entitlement = self.env["g2p.program.assessment"].get_res_field_name(res_model_entitlement)
        field_name_other = self.env["g2p.program.assessment"].get_res_field_name(res_model_other)

        self.assertEqual(field_name_membership, "program_membership_id")
        self.assertEqual(field_name_entitlement, "entitlement_id")
        self.assertIsNone(field_name_other)

    def test_compute_subject(self):
        res_model = "g2p.program_membership"
        res_id = self.membership.id

        subject = self.env["g2p.program.assessment"].compute_subject(res_model, res_id)

        self.assertTrue(subject)
        self.assertIn("Assessment", subject)

    def test_compute_program_memberships(self):
        result = self.env["g2p.program.assessment"].compute_program_memberships(
            "g2p.program_membership", self.membership.id
        )
        self.assertEqual(result, self.membership)

        result = self.env["g2p.program.assessment"].compute_program_memberships(
            "g2p.entitlement", self.entitlement.id
        )
        expected_membership = self.env["g2p.program_membership"].search(
            [
                ("partner_id", "=", self.partner.id),
                ("program_id", "=", self.program.id),
            ]
        )
        self.assertEqual(result, expected_membership)

        result = self.env["g2p.program.assessment"].compute_program_memberships("unknown_model", 0)
        self.assertIsNone(result)
