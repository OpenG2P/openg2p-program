from odoo import fields, models


class G2pSponsoringBankAccount(models.Model):
    _name = "g2p.sponsoring.bank.account"
    _description = "S2p Sponsoring Bank Account"



    name = fields.Char("Bank name")
    bank_code = fields.Char()
    account_number = fields.Char()
    bank_branch = fields.Char()