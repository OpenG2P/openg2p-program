# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentManager(models.Model):
    _inherit = "g2p.program.payment.manager"

    @api.model
    def _selection_manager_ref_id(self):
        selection = super()._selection_manager_ref_id()
        new_manager = (
            "g2p.program.payment.manager.simple.mpesa",
            "Simple MPesa Payment Manager",
        )
        if new_manager not in selection:
            selection.append(new_manager)
        return selection


class G2PPaymentManagerSimpleMpesa(models.Model):
    _name = "g2p.program.payment.manager.simple.mpesa"
    _inherit = ["g2p.program.payment.manager.default",
                "mail.thread",
                "mail.activity.mixin"]
    _description = "Simple MPesa Payment Manager"

    batch_tag_ids = fields.Many2many(
        "g2p.payment.batch.tag",
        "g2p_pay_batch_tag_pay_manager_simple_mpesa",
        string="Batch Tags",
        ondelete="cascade",
    )

    create_batch = fields.Boolean("Automatically Create Batch", default=True)
    payee_id_type = fields.Selection(
            [
                ("bank_acc_no", "Bank Account Number"),
                ("bank_acc_iban", "IBAN"),
                ("phone", "Phone"),
                ("email", "Email"),
                ("reg_id", "Registrant ID"),
                ],
                "Payee ID Field",
                required=True,
    )
    reg_id_type_for_payee_id = fields.Many2one(
        "g2p.id.type", "Payee DFSP ID Type", required=False
    )
    customer_type = fields.Char(default = "subscriber")

    auth_endpoint_url = fields.Char("Authentication Endpoint URL", required=True)
    payment_endpoint_url = fields.Char("Payment Endpoint URL", required=True)

    username = fields.Char(required=True)
    password = fields.Char(required=True)

    def _send_payments(self, batches):
        # Transfer to Simple Mpesa
        _logger.info("DEBUG! send_payments Manager: Simple Mpesa.")
        for batch in batches:
            if batch.batch_has_started:
                continue
            else:
                batch.batch_has_started = True

            # TODO: Implement Logic
            # Perform Auth Here
            try:
                data = {
                    "email": self.username,
                    "password": self.password
                }
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                response = requests.post(self.auth_endpoint_url, data=data, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                auth_token = response_data.get("token")

                for payment in batch.payment_ids:
                    payee_id_value = self._get_dfsp_id_and_type(payment)
                    amount = payment.amount_issued
                    auth_header = "Bearer " + auth_token
                    # Define the headers
                    headers = {
                        "Authorization": auth_header,
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                    data = {
                        "amount": amount,
                        "accountNo": payee_id_value,
                        "customerType": self.customer_type
                    }
                    try:
                        response = requests.post(self.payment_endpoint_url, headers=headers, data=data)            
                        _logger.info("MPesa Payment Transfer response", response.content)
                        response.raise_for_status()
                    except Exception as e:
                        _logger.error("Mpesa Payment Failed with unknown reason",e)
                        error_msg = "Mpesa Payment Failed during transfer with unknown reason"
                        self.message_post(body=error_msg, subject="Mpesa Payment Transfer")

            except Exception as e:
                _logger.error("Mpesa Payment Failed during authentication",e)
                error_msg = "Mpesa Payment Failed during authentication"
                self.message_post(body=error_msg, subject="Mpesa Payment Auth")

            batch.payment_ids.write({"state": "sent"})

    def _get_dfsp_id_and_type(self, payment):
        self.ensure_one()
        payee_id_type = self.payee_id_type
        if payee_id_type == "bank_acc_no":
            # TODO: Compute which bank_acc_no to choose from bank account list
            for bank_id in payment.partner_id.bank_ids:
                return bank_id.acc_number
        elif payee_id_type == "bank_acc_iban":
            # TODO: Compute which iban to choose from bank account list
            for bank_id in payment.partner_id.bank_ids:
                return bank_id.iban
        elif payee_id_type == "phone":
            return payment.partner_id.phone
        elif payee_id_type == "email":
            return payment.partner_id.email
        elif payee_id_type == "reg_id":
            for reg_id in payment.partner_id.reg_ids:
                if reg_id.id_type.id == self.reg_id_type_for_payee_id.id:
                    return reg_id.value
        # TODO: Deal with no bank acc and/or ID type not matching any available IDs
        return None

