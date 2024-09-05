import logging
import uuid
from datetime import datetime

import pyjq as jq

from odoo import fields, models

from odoo.addons.g2p_openid_vci.json_encoder import VCJSONEncoder

_logger = logging.getLogger(__name__)


class BeneficiaryOpenIDVCIssuer(models.Model):
    _inherit = "g2p.openid.vci.issuers"

    issuer_type = fields.Selection(
        selection_add=[
            (
                "Beneficiary",
                "Beneficiary",
            )
        ],
        ondelete={"Beneficiary": "cascade"},
    )

    program_id = fields.Many2one("g2p.program")

    def issue_vc_Beneficiary(self, auth_claims, credential_request):
        self.ensure_one()
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")

        reg_id = (
            self.env["g2p.reg.id"]
            .sudo()
            .search(
                [
                    ("id_type", "=", self.auth_sub_id_type_id.id),
                    ("value", "=", auth_claims["sub"]),
                    (
                        "partner_id.program_membership_ids.program_id",
                        "=",
                        self.program_id.id,
                    ),
                ],
                limit=1,
            )
        )
        partner = None
        if not reg_id:
            raise ValueError(
                "ID not found in DB. "
                "Invalid Subject Received in auth claims. "
                "Or person not part of the program."
            )

        partner = reg_id.partner_id
        program_membership_id = partner.program_membership_ids.filtered(
            lambda x: x.program_id.id == self.program_id.id
        )
        if program_membership_id.state != "enrolled":
            raise ValueError("Person not enrolled into program.")

        partner_dict = partner.read()[0]
        program_membership_dict = program_membership_id.read()[0]
        reg_ids_dict = {reg_id.id_type.name: reg_id.read()[0] for reg_id in partner.reg_ids}
        program_dict = self.program_id.read()[0]

        curr_datetime = f'{datetime.utcnow().isoformat(timespec = "milliseconds")}Z'
        credential = jq.first(
            self.credential_format,
            VCJSONEncoder.python_dict_to_json_dict(
                {
                    "vc_id": str(uuid.uuid4()),
                    "web_base_url": web_base_url,
                    "issuer": self.read()[0],
                    "curr_datetime": curr_datetime,
                    "partner": partner_dict,
                    "partner_address": self.get_full_address(partner.address),
                    "partner_face": self.get_image_base64_data_in_url(partner.image_1920.decode()),
                    "reg_ids": reg_ids_dict,
                    "program_membership": program_membership_dict,
                    "program": program_dict,
                },
            ),
        )
        credential_response = {
            "credential": self.sign_and_issue_credential(credential),
            "format": credential_request["format"],
        }
        return credential_response

    def set_default_credential_type_Beneficiary(self):
        self.credential_type = "OpenG2PBeneficiaryVerifiableCredential"

    def set_from_static_file_Beneficiary(self, **kwargs):
        kwargs.setdefault("module_name", "g2p_openid_vci_programs")
        return self.set_from_static_file_Registry(**kwargs)
