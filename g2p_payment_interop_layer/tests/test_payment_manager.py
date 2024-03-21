from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("payment", "interop_layer")
class TestG2PPaymentInteropLayerManager(TransactionCase):
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

        self.payment_manager = self.env[
            "g2p.program.payment.manager.payment.interop.layer"
        ].create(
            {
                "name": "Interop Layer Payment Manager",
                "program_id": self.program.id,
                "payment_endpoint_url": "http://example.com/payment",
                "payee_id_type": "bank_acc_no",
                "create_batch": True,
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
                "entitlement_id": self.entitlement.id,
                "currency_id": self.env.ref("base.USD").id,
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
        # Test if the new manager is in the selection list
        selection = self.env["g2p.program.payment.manager"]._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.payment.interop.layer",
            "Payment Interoperability Layer",
        )
        self.assertIn(new_manager, selection)

    @patch("requests.post")
    def test_send_payments_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "payeeResults": [
                {
                    "status": "COMPLETED",
                    "amountCredited": 100.0,
                    "timestamp": "2022-01-01T00:00:00.000Z",
                }
            ]
        }
        mock_post.return_value = mock_response

        result = self.payment_manager._send_payments([self.payment_batch])

        # Check if the payments are marked as done
        self.assertEqual(self.payment.state, "reconciled")
        self.assertEqual(self.payment.status, "paid")
        self.assertEqual(self.payment.amount_paid, 100.0)

        # Check the result of the method
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["sticky"])
        self.assertEqual(result["params"]["type"], "success")
        self.assertEqual(
            result["params"]["next"]["type"], "ir.actions.act_window_close"
        )

    def test_send_payments_no_batches(self):
        # Test the _send_payments method when there are no payment batches to process

        # Call the _send_payments method with an empty list
        result = self.payment_manager._send_payments([])

        # Check the result of the method
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["sticky"])
        self.assertEqual(result["params"]["type"], "warning")
        self.assertEqual(result["params"]["message"], "No payment batches to process.")

    def test_get_dfsp_id_and_type(self):
        # Test for various payee_id_types
        payment = self.payment
        partner = self.partner

        payment_manager = self.payment_manager
        payment_manager.payee_id_type = "bank_acc_no"
        payment_manager.payee_id_type_to_send = "ACCOUNT_ID"

        # Create a partner and associate it with the bank account
        bank_account = self.env["res.partner.bank"].create(
            {"acc_number": "1234", "partner_id": partner.id}
        )
        partner.update({"bank_ids": [(4, bank_account.id)]})

        self.env["g2p.id.type"].create({"name": "ACCOUNT_ID"})

        payee_id_type, payee_id_value = payment_manager._get_dfsp_id_and_type(payment)
        self.assertEqual(payee_id_type, "ACCOUNT_ID")
        self.assertEqual(payee_id_value, "1234")

        payment_manager.payee_id_type = "phone"
        payment_manager.payee_id_type_to_send = "PHONE"
        partner.phone = "1234567890"

        payee_id_type, payee_id_value = payment_manager._get_dfsp_id_and_type(payment)
        self.assertEqual(payee_id_type, "PHONE")
        self.assertEqual(payee_id_value, "1234567890")

        # Test when no phone number exists
        partner.phone = None

        payee_id_type, payee_id_value = payment_manager._get_dfsp_id_and_type(payment)
        self.assertEqual(payee_id_type, "PHONE")
        self.assertEqual(payee_id_value, False)

    def test_send_payments_partial_success(self):
        # Test when some payments succeed and some fail
        self.payment_batch.update(
            {"payment_ids": [(4, self.payment.id), (4, self.payment2.id)]}
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "payeeResults": [
                {
                    "status": "COMPLETED",
                    "amountCredited": 50.0,
                    "timestamp": "2022-01-01T00:00:00.000Z",
                },
                {
                    "status": "REJECTED",
                    "amountCredited": 0.0,
                    "timestamp": "2022-01-01T00:00:00.000Z",
                },
            ]
        }
        with patch("requests.post", return_value=mock_response):
            result = self.payment_manager._send_payments([self.payment_batch])

        # Check if the successful payment is marked as paid
        self.assertEqual(self.payment.state, "reconciled")
        self.assertEqual(self.payment.status, "paid")
        self.assertEqual(self.payment.amount_paid, 50.0)

        # Check if the failed payment is marked as failed
        failed_payment = self.payment_batch.payment_ids.filtered(
            lambda p: p.status == "failed"
        )
        self.assertTrue(failed_payment)
        self.assertEqual(len(failed_payment), 1)

        failed_payment2 = self.payment_batch.payment_ids.filtered(
            lambda p: p.status == "failed"
        )
        self.assertTrue(failed_payment2)
        self.assertEqual(len(failed_payment2), 1)

        # Check the result of the method
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["sticky"])
        self.assertEqual(result["params"]["type"], "warning")
        self.assertIn("Payments sent successfully out of", result["params"]["message"])

    def test_send_payments_http_error(self):
        mock_post = MagicMock(side_effect=Exception("HTTP Error"))
        with patch("requests.post", mock_post):
            result = self.payment_manager._send_payments([self.payment_batch])

        self.assertEqual(self.payment.state, "issued")
        self.assertEqual(self.payment.status, False)

        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["sticky"])
        self.assertEqual(result["params"]["type"], "danger")

    def test_send_payments_other_error(self):
        mock_post = MagicMock(side_effect=ValueError("Other Error"))
        with patch("requests.post", mock_post):
            result = self.payment_manager._send_payments([self.payment_batch])

        self.assertEqual(self.payment.state, "issued")
        self.assertEqual(self.payment.status, False)

        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(result["params"]["sticky"])
        self.assertEqual(result["params"]["type"], "danger")
