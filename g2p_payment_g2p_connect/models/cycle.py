# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.g2p_programs.models import constants

_logger = logging.getLogger(__name__)


class G2PCycle(models.Model):
    _inherit = ["g2p.cycle"]

    disbursement_envelope_id = fields.Char("Disbursement Envelope ID")

    def generate_summary(self):
        # Call the Disbursement Envelope Status API to get the latest details
        try:
            program_manager = self.program_id.get_manager(constants.MANAGER_CYCLE)
            response = requests.post(
                program_manager.envelope_status_url,
                json={
                    "signature": "string",
                    "header": {
                        "version": "1.0.0",
                        "message_id": "string",
                        "message_ts": "string",
                        "action": "string",
                        "sender_id": "string",
                        "sender_uri": "",
                        "receiver_id": "",
                        "total_count": 0,
                        "is_msg_encrypted": False,
                        "meta": "string",
                    },
                    "message": self.disbursement_envelope_id,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            # Create new record for the summary report ( CycleEnvelopeSummary model)
            cycle_and_envelope_summary = self.env["g2p.cycle.envelope.summary"].create(
                {
                    "cycle_id": self.id,
                    "number_of_disbursements_received": data.get("message").get(
                        "number_of_disbursements_received"
                    ),
                    "total_disbursement_amount_received": data.get("message").get(
                        "total_disbursement_amount_received"
                    ),
                    "funds_available_with_bank": data.get("message").get("funds_available_with_bank"),
                    "funds_available_latest_timestamp": data.get("message").get(
                        "funds_available_latest_timestamp"
                    ),
                    "funds_available_latest_error_code": data.get("message").get(
                        "funds_available_latest_error_code"
                    ),
                    "funds_available_attempts": data.get("message").get("funds_available_attempts"),
                    "funds_blocked_with_bank": data.get("message").get("funds_blocked_with_bank"),
                    "funds_blocked_latest_timestamp": data.get("message").get(
                        "funds_blocked_latest_timestamp"
                    ),
                    "funds_blocked_latest_error_code": data.get("message").get(
                        "funds_blocked_latest_error_code"
                    ),
                    "funds_blocked_attempts": data.get("message").get("funds_blocked_attempts"),
                    "funds_blocked_reference_number": data.get("message").get(
                        "funds_blocked_reference_number"
                    ),
                    "id_mapper_resolution_required": data.get("message").get("id_mapper_resolution_required"),
                    "number_of_disbursements_shipped": data.get("message").get(
                        "number_of_disbursements_shipped"
                    ),
                    "number_of_disbursements_reconciled": data.get("message").get(
                        "number_of_disbursements_reconciled"
                    ),
                    "number_of_disbursements_reversed": data.get("message").get(
                        "number_of_disbursements_reversed"
                    ),
                }
            )
            # Return action to show the summary report
            return self.env.ref("g2p_payment_g2p_connect.action_generate_summary_extended").report_action(
                cycle_and_envelope_summary
            )

        except requests.exceptions.RequestException as e:
            raise UserError(_("Failed to fetch disbursement envelope status: %s" % e)) from e
