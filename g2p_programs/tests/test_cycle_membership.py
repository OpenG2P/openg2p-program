from odoo.exceptions import ValidationError
from odoo.tests import common


class TestG2PCycleMembership(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.cycle = cls.env["g2p.cycle"].create({"name": "Test Cycle"})
        cls.cycle_id = cls.cycle.id

    def test_create_cycle_membership(self):
        membership = self.env["g2p.cycle.membership"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
            }
        )
        self.assertTrue(membership)

    def test_duplicate_cycle_membership(self):
        self.env["g2p.cycle.membership"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["g2p.cycle.membership"].create(
                {
                    "partner_id": self.partner.id,
                    "cycle_id": self.cycle_id,
                }
            )

    def test_delete_draft_membership(self):
        membership = self.env["g2p.cycle.membership"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
            }
        )
        membership.unlink()
        self.assertFalse(membership.exists())

    def test_delete_approved_membership(self):
        membership = self.env["g2p.cycle.membership"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
                "state": "approved",
            }
        )
        with self.assertRaises(ValidationError):
            membership.unlink()

    def test_delete_approved_cycle(self):
        membership = self.env["g2p.cycle.membership"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
            }
        )
        self.cycle.state = "approved"
        with self.assertRaises(ValidationError):
            membership.unlink()

    def test_delete_approved_entitlement(self):
        membership = self.env["g2p.cycle.membership"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
            }
        )
        self.env["g2p.entitlement"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
                "state": "approved",
            }
        )
        with self.assertRaises(ValidationError):
            membership.unlink()

    def test_unlink_with_no_records(self):
        membership = self.env["g2p.cycle.membership"]
        membership.unlink()
        self.assertFalse(membership.exists())

    def test_compute_display_name(self):
        membership = self.env["g2p.cycle.membership"].create(
            {
                "partner_id": self.partner.id,
                "cycle_id": self.cycle_id,
            }
        )
        self.assertEqual(membership.display_name, f"[{self.cycle.name}] {self.partner.name}")
