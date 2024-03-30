from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("payment", "cash")
class TestG2PPaymentManagerCash(TransactionCase):
    def setUp(self):
        super().setUp()
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.cycle = self.env["g2p.cycle"].create(
            {
                "name": "Test Cycle",
                "program_id": self.program.id,
                "start_date": fields.Datetime.now(),
                "end_date": fields.Datetime.now() + timedelta(days=7),
            }
        )
        self.entitlement = self.env["g2p.entitlement"].create(
            {
                "program_id": self.program.id,
                "partner_id": self.partner.id,
                "cycle_id": self.cycle.id,
                "state": "draft",
                "initial_amount": 100.00,
            }
        )
        self.payment_manager = self.env["g2p.program.payment.manager.cash"].create(
            {
                "name": "Cash Payment Manager",
                "program_id": self.program.id,
            }
        )

        self.payment = self.env["g2p.payment"].create(
            {
                "name": "Test Payment",
                "amount_issued": 100.0,
                "cycle_id": self.cycle.id,
                "state": "issued",
                "entitlement_id": self.entitlement.id,
            }
        )

        self.payment_batch = self.env["g2p.payment.batch"].create(
            {
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "payment_ids": [(4, self.payment.id)],
            }
        )

    def test_selection_manager_ref_id(self):
        selection = self.env["g2p.program.payment.manager"]._selection_manager_ref_id()
        self.assertIn(("g2p.program.payment.manager.cash", "Cash Payment Manager"), selection)

    def test_crypto_key_set_creation(self):
        crypto_key_set = self.env["g2p.crypto.key.set"].create(
            {
                "name": "Test Crypto Key Set",
                "cash_payment_manager_id": self.payment_manager.id,
            }
        )
        self.assertEqual(crypto_key_set.cash_payment_manager_id, self.payment_manager)

    def test_send_payments(self):
        result = self.payment_manager._send_payments([self.payment_batch])
        self.assertEqual(self.payment.state, "reconciled")
        self.assertEqual(self.payment.status, "paid")
        self.assertEqual(self.payment.amount_paid, 100.0)

        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["sticky"])
        self.assertEqual(result["params"]["type"], "success")
        self.assertEqual(result["params"]["next"]["type"], "ir.actions.act_window_close")

    def test_send_payments_no_batches(self):
        result = self.payment_manager._send_payments([])

        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["sticky"])
        self.assertEqual(result["params"]["type"], "warning")
        self.assertEqual(result["params"]["message"], "No payment batches to process.")
