from odoo import api, fields, models


class G2pSponsoringBankAccount(models.Model):
    _name = "g2p.sponsoring.bank.account"
    _description = "S2p Sponsoring Bank Account"

    name = fields.Char()
    account_name = fields.Char()
    bank_code = fields.Char()
    account_number = fields.Char()
    bank_branch = fields.Char("Account branch")

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        res.name = res.account_name + "-" + res.bank_branch
        return res
