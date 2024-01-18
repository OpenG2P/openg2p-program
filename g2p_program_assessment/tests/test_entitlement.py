from datetime import datetime, timedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PAssessmentEntitlement(TransactionCase):
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

        cls.cycle_beneficiary = cls.env["g2p.cycle.membership"].create(
            {
                "partner_id": cls.partner.id,
                "cycle_id": cls.cycle.id,
                "state": "enrolled",
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

    def test_copy_assessments_from_beneficiary(self):
        previous_entitlement = self.env["g2p.entitlement"].create(
            {
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "create_date": datetime.now() - timedelta(days=5),
                "initial_amount": 500.0,
                "is_cash_entitlement": True,
                "state": "draft",
            }
        )

        res_model = "g2p.program_membership"
        res_id = self.membership.id

        assessment1 = self.env["g2p.program.assessment"].post_assessment(
            "This is a test assessment1.",
            res_model,
            res_id,
            is_comment=False,
            subject="Test Subject",
            message_type="comment",
            subtype_id=None,
            partner_ids=None,
            record_name="Test Record",
        )
        assessment2 = self.env["g2p.program.assessment"].post_assessment(
            "This is a test assessment2.",
            res_model,
            res_id,
            is_comment=False,
            subject="Test Subject",
            message_type="comment",
            subtype_id=None,
            partner_ids=None,
            record_name="Test Record",
        )

        self.entitlement.copy_assessments_from_beneficiary()

        self.assertEqual(len(self.entitlement.assessment_ids), 2)
        self.assertIn(assessment1, self.entitlement.assessment_ids)
        self.assertIn(assessment2, self.entitlement.assessment_ids)

    def test_prepare_entitlements(self):
        beneficiaries = self.cycle_beneficiary
        self.env["g2p.program.entitlement.manager.default"].prepare_entitlements(
            self.cycle, beneficiaries
        )
