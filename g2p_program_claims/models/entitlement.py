from odoo import _, fields, models


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    vendor_id = fields.Many2one("res.partner")

    claim_original_entitlement_id = fields.Many2one(
        "g2p.entitlement", string="Original Entitlement of this Claim"
    )

    claim_entitlement_ids = fields.One2many(
        "g2p.entitlement", "claim_original_entitlement_id"
    )

    def _compute_name(self):
        for record in self:
            name = (
                _("Entitlement")
                if not record.program_id.is_claims_program
                else _("Claim")
            )
            initial_amount = "{:,.2f}".format(record.initial_amount)
            if record.is_cash_entitlement:
                name += (
                    " Cash ["
                    + str(record.currency_id.symbol)
                    + " "
                    + initial_amount
                    + "]"
                )
            else:
                name += " (" + str(record.code) + ")"
            record.name = name
