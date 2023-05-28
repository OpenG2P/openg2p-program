from odoo import _, fields, models


class G2PEntitlement(models.Model):
    _inherit = "g2p.entitlement"

    service_provider_id = fields.Many2one("res.partner")

    reimbursement_original_entitlement_id = fields.Many2one(
        "g2p.entitlement", string="Original Entitlement of this Reimbursement"
    )

    reimbursement_entitlement_ids = fields.One2many(
        "g2p.entitlement", "reimbursement_original_entitlement_id"
    )

    def _compute_name(self):
        for record in self:
            name = (
                _("Entitlement")
                if not record.program_id.is_reimbursement_program
                else _("Reimbursement")
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

    def active_cycle(self):
        reimbursement_program = self.program_id.reimbursement_program_id
        if not reimbursement_program.default_active_cycle.id:
            reimbursement_program.create_new_cycle()

            cycle_id = self.env["g2p.cycle"].search(
                [("program_id", "=", reimbursement_program.id)]
            )
            return cycle_id.id

        return reimbursement_program.default_active_cycle.id

    def submit_reimbursement_claim(
        self,
        partner,
        received_code,
        supporting_document_file_ids=None,
        amount=None,
        transfer_fee=None,
    ):
        # return error_code, entitlement
        self.ensure_one()

        # TODO: Check if beneficiary of reimbursement program

        if not self.code == received_code:
            return 2, None

        reimbursement_program = self.program_id.reimbursement_program_id

        # TODO: Remove this hardcode of default_active_cycle.
        # This should come from reimbursement_cycle <--> program_cycle mapping
        reimbursement_cycle = reimbursement_program.default_active_cycle

        return (
            self.env["g2p.entitlement"]
            .sudo()
            .create(
                {
                    "cycle_id": self.active_cycle(),
                    "partner_id": partner.id,
                    "initial_amount": amount if amount else self.initial_amount,
                    "transfer_fee": transfer_fee if transfer_fee else self.transfer_fee,
                    "currency_id": reimbursement_program.journal_id.currency_id.id,
                    "state": "draft",
                    "is_cash_entitlement": True,
                    "valid_from": reimbursement_cycle.start_date,
                    "valid_until": reimbursement_cycle.end_date,
                    "supporting_document_ids": supporting_document_file_ids,
                    "reimbursement_original_entitlement_id": self.id,
                }
            )
        )
