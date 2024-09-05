from odoo.exceptions import UserError
from odoo.tests import common

from odoo.addons.g2p_programs.models import constants


class TestDefaultProgramManager(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.manager = self.program.get_manager(constants.MANAGER_PROGRAM)

    def test_onchange_is_cycless_not_original_manager(self):
        new_manager = self.env["g2p.program.manager.default"].create(
            {
                "program_id": self.program.id,
                "name": "Manager",
            }
        )

        new_manager.is_cycleless = True
        new_manager.onchange_is_cycless()
        self.assertFalse(self.program.is_cycleless)

    def test_onchange_is_cycleless_no_enrolled_registrants(self):
        with self.assertRaises(UserError):
            self.manager.is_cycleless = True
