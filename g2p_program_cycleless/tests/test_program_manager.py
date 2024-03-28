from odoo.exceptions import UserError
from odoo.tests import common

from odoo.addons.g2p_programs.models import constants


class TestDefaultProgramManager(common.TransactionCase):
    def setUp(self):
        super(TestDefaultProgramManager, self).setUp()

        # Create a program and enroll a registrant (required for create_new_cycle)
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.membership = self.env["g2p.program_membership"].create(
            {
                "program_id": self.program.id,
                "partner_id": self.partner.id,
                "state": "active",
            }
        )

        # Create the default program manager for the program
        self.manager = self.program.get_manager(constants.MANAGER_PROGRAM)

    def test_onchange_is_cycless_true(self):
        self.manager.is_cycleless = True

        # Assert program's is_cycleless field is also set to True
        self.assertEqual(self.program.is_cycleless, True)

    def test_onchange_is_cycless_false(self):
        # Create a cycle to test for its removal
        self.program.create_new_cycle()

        self.manager.is_cycleless = True  # Set cycleless to True to create a cycle
        self.manager.onchange_is_cycless()

        self.manager.is_cycleless = False

        # Assert program's is_cycleless field is also set to False
        self.assertEqual(self.program.is_cycleless, False)

        # Assert the previously created cycle is removed
        with self.assertRaises(AssertionError):
            self.program.default_active_cycle

    def test_onchange_is_cycless_not_original_manager(self):
        # Create another program manager with a name
        new_manager = self.env["g2p.program.manager.default"].create(
            {
                "program_id": self.program.id,
                "name": "Another Manager",
            }
        )

        new_manager.is_cycleless = True
        new_manager.onchange_is_cycless()

        # Assert changing is_cycleless on a non-original manager has no effect
        self.assertFalse(self.program.is_cycleless)

    def test_onchange_is_cycleless_no_enrolled_registrants(self):
        # Set manager to cycleless without enrolled registrants
        with self.assertRaises(UserError):
            self.manager.is_cycleless = True
            self.manager.onchange_is_cycless()
