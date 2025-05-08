import json
import logging

import requests

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PPaymentManagerG2PConnect(models.Model):
    _inherit = "g2p.program.payment.manager.g2p.connect"

    program_creation_endpoint_url = fields.Char("Program Creation URL", required=False)
    sponsoring_bank = fields.Many2one("g2p.sponsoring.bank.account", required=False)
    sent_to_bridge = fields.Boolean(default=False)

    def publish_bridge_benefit_program(self):
        self.ensure_one()
        try:
            url = self.program_creation_endpoint_url
            data = {
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
                    "benefit_program_mnemonic": f"{self.program_id.name} #{self.id}",
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

            token = self.create_jwt_token(json.dumps(data, separators=(",", ":")))
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Signature": token,
            }
            response = requests.post(url, data=json.dumps(data), headers=headers, timeout=self.api_timeout)
            response.raise_for_status()
            response_data = response.json()
            status = response_data.get("header", {}).get("status")
            reason = response_data.get("header", {}).get("status_reason_message")
            if response_data.get("header", {}).get("status") == "succ":
                self.sent_to_bridge = True
            else:
                raise ValidationError(f"Request has the {status} status because of {reason}")

        except Exception:
            _logger.exception("Error occurred on publishing sponsoring bank")
            raise
