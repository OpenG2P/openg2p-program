from odoo import api, fields, models

from odoo.addons.g2p_programs.models import constants


class DefaultProgramManager(models.Model):
    _inherit = "g2p.program.manager.default"

    is_cycleless = fields.Boolean(help="Mark this to make the program Cycleless")

    @api.constrains("is_cycleless")
    def onchange_is_cycless(self):
        orig_prog_man = self.program_id.get_manager(constants.MANAGER_PROGRAM)
        if self.id == orig_prog_man.id:
            self.program_id.is_cycleless = self.is_cycleless
            if self.is_cycleless and not self.program_id.default_active_cycle:
                self.program_id.create_new_cycle()
