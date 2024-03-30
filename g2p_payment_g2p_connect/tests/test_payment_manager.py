from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestG2PConnectPaymentManager(TransactionCase):
    def setUp(self):
        super().setUp()
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.manager = self.env["g2p.program.payment.manager.g2p.connect"].create(
            {
                "name": "G2P Connect Payment Manager",
                "payment_endpoint_url": "http://example.com/payment",
                "status_endpoint_url": "http://example.com/status",
                "program_id": self.program.id,
                "payee_id_type": "bank_acc_no",
                "create_batch": True,
                "locale": "en_US",
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.partner2 = self.env["res.partner"].create({"name": "Test Partner2"})
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
        self.entitlement2 = self.env["g2p.entitlement"].create(
            {
                "program_id": self.program.id,
                "partner_id": self.partner2.id,
                "cycle_id": self.cycle.id,
                "state": "draft",
                "initial_amount": 100.00,
            }
        )
        self.payment = self.env["g2p.payment"].create(
            {
                "name": "Test Payment",
                "amount_issued": 100.0,
                "cycle_id": self.cycle.id,
                "state": "issued",
                "entitlement_id": self.entitlement.id,
                "currency_id": self.env.ref("base.USD").id,
            }
        )
        self.payment2 = self.env["g2p.payment"].create(
            {
                "name": "Test Payment2",
                "amount_issued": 100.0,
                "cycle_id": self.cycle.id,
                "state": "issued",
                "entitlement_id": self.entitlement2.id,
                "currency_id": self.env.ref("base.USD").id,
            }
        )

        self.batch = self.env["g2p.payment.batch"].create(
            {
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "payment_ids": [(4, self.payment.id)],
            }
        )

    def test_send_payments_success(self):
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            self.manager._send_payments(self.env["g2p.payment.batch"].browse(self.batch.id))

    def test_send_payments_other_error(self):
        with patch("requests.post") as mock_post:
            mock_post.side_effect = ValueError("Other Error")
            self.manager._send_payments(self.env["g2p.payment.batch"].browse(self.batch.id))

    def test_payments_status_check(self):
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {
                    "txnstatus_response": {
                        "txn_status": [
                            {
                                "status": "succ",
                                "reference_id": "Test Payment",
                                "amount": 100.0,
                            },
                            {
                                "status": "rjct",
                                "reference_id": "Test Payment2",
                                "amount": 100.0,
                            },
                        ]
                    }
                },
            }
            mock_post.return_value = mock_response
            self.manager.payments_status_check(self.manager.id)

            self.assertEqual(self.payment.state, "reconciled")
            self.assertEqual(self.payment.status, "paid")
            self.assertEqual(self.payment.amount_paid, 0.0)

            self.assertEqual(self.payment2.state, "reconciled")
            self.assertEqual(self.payment2.status, "failed")
            self.assertEqual(self.payment2.amount_paid, 0.0)

            self.manager.stop_status_check_cron()
            self.assertFalse(self.manager.status_check_cron_id)

    def test_payments_status_check_other_error(self):
        with patch("requests.post") as mock_post:
            mock_post.side_effect = ValueError("Other Error")
            self.manager.payments_status_check(self.manager.id)

    def test_stop_status_check_cron(self):
        self.manager.stop_status_check_cron()
        self.assertFalse(self.manager.status_check_cron_id)

    def test_get_payee_fa(self):
        self.manager.payee_id_type = "bank_acc_no"
        self.manager._get_payee_fa(self.payment)

        self.manager.payee_id_type = "bank_acc_iban"
        self.manager._get_payee_fa(self.payment)

        self.manager.payee_id_type = "phone"
        self.manager._get_payee_fa(self.payment)

        self.manager.payee_id_type = "email"
        self.manager._get_payee_fa(self.payment)

        self.manager.payee_id_type = "reg_id"
        reg_id_type = self.env["g2p.id.type"].create({"name": "Test ID Type"})
        self.manager.reg_id_type_for_payee_id = reg_id_type
        reg_id_value = "Test Reg ID"
        self.payment.partner_id.reg_ids = [(0, 0, {"id_type": reg_id_type.id, "value": reg_id_value})]
        self.manager._get_payee_fa(self.payment)

    def test_update_batch_completion(self):
        self.assertFalse(self.batch.batch_has_completed)

        self.payment.state = "reconciled"
        self.payment.status = "paid"
        self.batch.batch_has_started = True
        self.batch.batch_has_completed = False

        self.manager.payments_status_check(self.manager.id)
        self.assertEqual(self.batch.batch_has_completed, True)
