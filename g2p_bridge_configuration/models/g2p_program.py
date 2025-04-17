import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from jose import jwt

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2pProgram(models.Model):
    _inherit = "g2p.program"

    sponsoring_bank = fields.Many2one("g2p.sponsoring.bank.account")
    send_to_bridge = fields.Boolean()

    @api.model
    def create(self, vals):
        name = vals.get("name")
        if name:
            existing = self.env["g2p.program"].sudo().search([("name", "=", name)], limit=1)
            if existing:
                raise ValidationError(_(f"A record with the name '{name}' already exists."))
        res = super().create(vals)
        return res

    def load_env(self):
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)

    def create_jwt_token(self, payload):
        private_key = os.getenv("JWT_PRIVATE_KEY")
        headers = {"alg": "RS256", "typ": "JWT"}
        payload = json.loads(payload)  # Don't skip this
        token = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)
        return token

    def publish_bridge_benefit_program(self):
        try:
            self.load_env()
            payment_manager = self.env["g2p.program.payment.manager.g2p.connect"].search(
                [("create_batch", "=", True)], limit=1
            )
            if not payment_manager:
                raise ValidationError(_("Please create payment manager."))
            if not self.sponsoring_bank:
                raise ValidationError(_("Please select sponsor bank."))
            url = payment_manager.payment_endpoint_url + "/create_benefit_program_configuration"
            data = {
                "signature": "string",
                "header": {
                    "version": "1.0.0",
                    "message_id": "string",
                    "message_ts": "string",
                    "action": "string",
                    "sender_id": os.getenv("sender_id"),
                    "sender_uri": "",
                    "receiver_id": "",
                    "total_count": 0,
                    "is_msg_encrypted": False,
                    "meta": "string",
                },
                "message": {
                    "benefit_program_mnemonic": self.name,
                    "benefit_program_name": self.name,
                    "funding_org_code": self.env.user.company_id.name,
                    "funding_org_name": self.env.user.company_id.name,
                    "sponsor_bank_code": self.sponsoring_bank.bank_code,
                    "sponsor_bank_account_number": self.sponsoring_bank.account_number,
                    "sponsor_bank_branch_code": self.sponsoring_bank.bank_branch,
                    "sponsor_bank_account_currency": self.env.user.company_id.currency_id.name,
                    "id_mapper_resolution_required": True,
                },
            }
            token = self.create_jwt_token(json.dumps(data))
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": token,
            }
            response = requests.post(
                url, data=json.dumps(data), headers=headers, timeout=payment_manager.api_timeout
            )
            response.raise_for_status()
            response_data = response.json()
            if response_data.get("header", {}).get("status") == "succ":
                self.send_to_bridge = True
        except Exception as e:
            _logger.error("Error occurred on publishing sponsoring bank %s" % e)
