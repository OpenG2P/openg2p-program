# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.voucher",
            "Voucher Payment Manager",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PFilesPaymentManager(models.Model):
    _name = "g2p.program.payment.manager.file"
    _inherit = [
        "g2p.base.program.payment.manager",
        "g2p.manager.source.mixin",
    ]
    _description = "File based Payment Manager"
