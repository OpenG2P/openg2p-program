from odoo import api, fields, models


class G2PSponsoringBankAccount(models.Model):
    _name = "g2p.sponsoring.bank.account"
    _description = "G2P Sponsoring Bank Account"

    name = fields.Char()
    account_name = fields.Char()
    bank_code = fields.Char()
    account_number = fields.Char()
    bank_branch = fields.Char("Account branch")

    @api.constrains("account_name", "bank_branch")
    def _constrains_entitlement_id(self):
        for rec in self:
            rec.name = f"{rec.account_name}-{rec.bank_branch}"
