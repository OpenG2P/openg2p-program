from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.g2p_programs.models import constants


@tagged("post_install", "-at_install")
class TestG2PEntitlement(TransactionCase):
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
        cash_pay_mgr_obj = "g2p.program.payment.manager.cash"
        pay_file_config = self.env["g2p.payment.file.config"].create({"name": "Payment file config"})
        self.cash_mgr = self.env[cash_pay_mgr_obj].create(
            {
                "name": "Cash Manager",
                "program_id": self.program.id,
                "payment_file_config_ids": [(4, pay_file_config.id)],
            }
        )

    def test_compute_show_payment_buttons_valid(self):
        self.program.get_manager(constants.MANAGER_PAYMENT).unlink()
        pay_manager = self.env["g2p.program.payment.manager"].create(
            {
                "program_id": self.program.id,
                "manager_ref_id": self.cash_mgr,
            }
        )
        self.program.update({"payment_managers": [(4, pay_manager.id)]})
        self.entitlement.state = "approved"
        self.entitlement._compute_show_payment_buttons()
        self.assertTrue(self.entitlement.show_payment_prepare)

    def test_prepare_and_send_payment_cash_not_approved(self):
        self.entitlement.state = "draft"
        action = self.entitlement.prepare_and_send_payment_cash()
        self.assertEqual(action["params"]["type"], "danger")
        self.assertEqual(action["params"]["title"], "Payment")
        self.assertEqual(action["params"]["message"], "Entitlement is not approved!")

    def test_prepare_and_send_payment_cash_already_paid(self):
        self.entitlement.payment_status = "paid"
        self.entitlement.state = "approved"
        action = self.entitlement.prepare_and_send_payment_cash()
        self.assertEqual(action["params"]["type"], "danger")
        self.assertEqual(action["params"]["title"], "Payment")
        self.assertEqual(action["params"]["message"], "Invalid operation!")

    def test_prepare_and_send_payment_cash_valid(self):
        self.program.get_manager(constants.MANAGER_PAYMENT).unlink()
        pay_manager = self.env["g2p.program.payment.manager"].create(
            {
                "program_id": self.program.id,
                "manager_ref_id": self.cash_mgr,
            }
        )
        self.program.update({"payment_managers": [(4, pay_manager.id)]})
        self.entitlement.state = "approved"
        action = self.entitlement.prepare_and_send_payment_cash()
        self.assertEqual(action["params"]["type"], "success")
        self.assertEqual(action["params"]["title"], "Payment")
        self.assertEqual(action["params"]["message"], "Payment was issued and sent.")
