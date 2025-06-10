# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PDatashareConfigRabbitMQProgram(models.Model):
    _inherit = "g2p.datashare.config.rabbitmq"

    data_source = fields.Selection(
        selection_add=[
            (
                "beneficiary_registry",
                "Beneficiary Registry",
            )
        ],
        ondelete={"beneficiary_registry": "cascade"},
    )

    program_id = fields.Many2one("g2p.program")
