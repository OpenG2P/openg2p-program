from odoo import fields, models, api, _
import requests
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)



class G2pProgram(models.Model):
    _inherit = "g2p.program"

    sponsoring_bank = fields.Many2one('g2p.sponsoring.bank.account')
    send_to_bridge = fields.Boolean()

    def publish_to_api(self):
        try:
            payment_manager = self.env['g2p.program.payment.manager.g2p.connect'].search([('create_batch', '=', True)],limit=1)
            if not payment_manager:
                raise ValidationError("Please create payment manager.")
            if not self.sponsoring_bank:
                raise ValidationError("Please select sponsor bank.")
            url = payment_manager.payment_endpoint_url +'/create_benefit_program_configuration'

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "benefit_program_mnemonic": self.name,
                "benefit_program_name": self.name,
                "funding_org_code": self.env.user.company_id.name,
                "funding_org_name": self.env.user.company_id.name,
                "sponsor_bank_code": self.sponsoring_bank.bank_code,
                "sponsor_bank_account_number": self.sponsoring_bank.account_number,
                "sponsor_bank_branch_code": self.sponsoring_bank.bank_branch,
                "sponsor_bank_account_currency": self.env.user.company_id.currency_id.name,
                "id_mapper_resolution_required": True
            }
            response = requests.post(
                url,
                data=data,
                headers = headers,
            )
            response.raise_for_status()
            response_data = response.json()
            self.send_to_bridge = True
        except Exception as e:
            _logger.error("Error occurred on publishing sponsoring bank %s" % e)
