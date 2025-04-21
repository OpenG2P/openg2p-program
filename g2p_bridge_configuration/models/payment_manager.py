import json
import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PPaymentManagerG2PConnect(models.Model):
    _inherit = "g2p.program.payment.manager.g2p.connect"

    program_creation_endpoint_url = fields.Char("Program Creation URL", required=False)
    sponsoring_bank = fields.Many2one("g2p.sponsoring.bank.account", required=False)
    sent_to_bridge = fields.Boolean(default=False)
    sender_id = fields.Char("Sender ID", required=False)

    def create_jwt_token(self, payload: dict):
        self.ensure_one()
        enc_provider = self.get_encryption_provider()
        token = enc_provider.jwt_sign(payload, include_payload=False)
        return token

    def _check_duplicate_program_name(self):
        if self.program_id:
            program = self.env["g2p.program"].search(
                [("name", "=", self.program_id.name), ("id", "!=", self.program_id.id)]
            )
            if program:
                raise ValidationError(_("The program already exists. Please choose another program."))

    def publish_bridge_benefit_program(self):
        self.ensure_one()
        self._check_duplicate_program_name()
        try:
            url = self.program_creation_endpoint_url
            data = {
                "signature": "string",
                "header": {
                    "version": "1.0.0",
                    "message_id": "string",
                    "message_ts": "string",
                    "action": "string",
                    "sender_id": self.sender_id,
                    "sender_uri": "",
                    "receiver_id": "",
                    "total_count": 0,
                    "is_msg_encrypted": False,
                    "meta": "string",
                },
                "message": {
                    "benefit_program_mnemonic": self.program_id.name,
                    "benefit_program_name": self.program_id.name,
                    "funding_org_code": self.program_id.company_id.name,
                    "funding_org_name": self.program_id.company_id.name,
                    "sponsor_bank_code": self.sponsoring_bank.bank_code,
                    "sponsor_bank_account_number": self.sponsoring_bank.account_number,
                    "sponsor_bank_branch_code": self.sponsoring_bank.bank_branch,
                    "sponsor_bank_account_currency": self.currency_id.name,
                    "id_mapper_resolution_required": True,
                },
            }
            token = self.create_jwt_token(data)
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Signature": token,
            }
            response = requests.post(url, data=json.dumps(data), headers=headers, timeout=self.api_timeout)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get("header", {}).get("status") == "succ":
                self.sent_to_bridge = True
        except Exception as e:
            _logger.error("Error occurred on publishing sponsoring bank %s" % e)
