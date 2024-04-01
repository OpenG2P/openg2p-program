from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestG2PPaymentManager(TransactionCase):
    def setUp(self):
        super(TestG2PPaymentManager, self).setUp()
        self.backend = self.env["storage.backend"].create({"name": "Test Backend"})
        self.crypto_key_set = self.env["g2p.crypto.key.set"].create(
            {"name": "Test Crypto Key"}
        )
        self.file_config = self.env["g2p.payment.file.config"].create(
            {"name": "Test Config"}
        )
        self.batch_tag = self.env["g2p.payment.batch.tag"].create(
            {
                "name": "Test Batch Tag",
                "file_config_ids": [(6, 0, [self.file_config.id])],
            }
        )
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
                "state": "approved",
                "initial_amount": 100.00,
            }
        )

        self.files_payment_manager = self.env[
            "g2p.program.payment.manager.file"
        ].create(
            {
                "name": "Test Files Payment Manager",
                "file_document_store": self.backend.id,
                "crypto_key_set": [
                    (0, 0, {"name": "Key Set for File Payment Manager"})
                ],
                "batch_tag_ids": [(6, 0, [self.batch_tag.id])],
                "program_id": self.program.id,
                "create_batch": True,
            }
        )
        self.program_payment_manager = self.env["g2p.program.payment.manager"].create(
            {
                "manager_ref_id": self.files_payment_manager,
            }
        )

    def test_payment_manager_creation(self):
        self.assertTrue(self.files_payment_manager)
        self.assertEqual(
            self.files_payment_manager.file_document_store.id, self.backend.id
        )
        self.assertEqual(len(self.files_payment_manager.crypto_key_set), 1)
        self.assertIn(self.batch_tag.id, self.files_payment_manager.batch_tag_ids.ids)

    def test_prepare_payments_with_batch(self):
        payments, batches = self.files_payment_manager._prepare_payments(
            self.cycle, self.entitlement
        )

        self.assertEqual(len(payments), 1, "Should create one payment")
        self.assertEqual(len(batches), 1, "Should create one batch")
        self.assertTrue(batches[0].tag_id.id, self.batch_tag.id)
        self.assertEqual(payments[0].amount, 100.00)
        self.assertEqual(payments[0].cycle_id.id, self.cycle.id)

    def test_prepare_payments_without_batch(self):
        self.files_payment_manager.write({"create_batch": False})
        payments, batches = self.files_payment_manager._prepare_payments(
            self.cycle, self.entitlement
        )

        self.assertEqual(len(payments), 1, "Should create one payment")

        self.assertEqual(payments[0].amount_issued, 100.00)
        self.assertEqual(payments[0].cycle_id.id, self.cycle.id)

    def test_send_payments(self):
        with self.assertRaises(NotImplementedError):
            self.files_payment_manager._send_payments(self.batch_tag)

    def test_selection_manager_ref_id(self):
        selection = self.program_payment_manager._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.file",
            "File Payment Manager",
        )
        self.assertIn(new_manager, selection)

    def test_create_method(self):
        files_payment_manager = self.env["g2p.program.payment.manager.file"].create(
            {
                "name": "Test Files Payment Manager Without Crypto Key Set",
                "file_document_store": self.backend.id,
                "program_id": self.program.id,
                "create_batch": True,
            }
        )
        self.assertEqual(len(files_payment_manager.crypto_key_set), 1)

    def test_batch_tag_model_inheritance(self):
        batch_tag = self.env["g2p.payment.batch.tag"].create(
            {
                "name": "Test Batch Tag with Render Files Per Payment",
                "render_files_per_payment": True,
            }
        )
        self.assertTrue(batch_tag.render_files_per_payment)
