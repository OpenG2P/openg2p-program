
import uuid
from odoo import api, fields, models

class G2PCryptoKeySet(models.Model):
    _name = "g2p.crypto.key.set"
    _description = "G2P Crypto Key Set"

    _order = "id desc"


    # name = fields.Char(string="kid", required=True)

    # type = fields.Selection(
    #     [
    #         ("rsa", "RSA"),
    #     ],
    #     default="rsa",
    # )

    # size = fields.Selection(
    #     [
    #         ("2048", "2048"),
    #         ("3072", "3072"),
    #         ("4096", "4096"),
    #     ],
    #     default="2048",
    # )

    # priv_key = fields.Char(compute="_compute_priv_key", store=True)
    # pub_cert = fields.Char(compute="_compute_pub_cert", store=True)

    jwk = fields.Char(compute="_compute_jwk", store=True)

    # use = fields.Selection(
    #     [
    #         ("sig", "Signature"),
    #         ("enc", "Encryption"),
    #     ],
    #     default="sig",
    # )
    status = fields.Selection(
        [
            ("active", "Active"),
        ],
        default="active",
    )

    file_payment_manager_id = fields.Many2one(
        "g2p.program.payment.manager.file", ondelete="cascade"
    )

    _sql_constraints = [
        (
            "name_unique",
            "unique (name)",
            "Name/KID of the key set should be unique",
        ),
    ]
    @api.model
    def create(self, values):
        if not values.get("name", None):
            values["name"] = str(uuid.uuid4())
        return super(G2PCryptoKeySet, self).create(values)

    # @api.depends("type", "size")
    # def _compute_priv_key(self):
    #     for rec in self:
    #         if rec.type == "rsa":
    #             priv_key_data = self.get_encryption_public_key()  
    #             rec.priv_key = priv_key_data.get("private_key")

    # @api.depends("priv_key")
    # def _compute_pub_cert(self):
    #     for rec in self:
    #         if rec.type == "rsa":
    #             pub_key_data = self.get_signing_public_key() 
    #             rec.pub_cert = pub_key_data.get("public_key")

    # def get_signing_public_key(self):
    #     url = f"{self.base_url}/tpmsigning/publickey"
    #     headers = {"Authorization": f"Bearer {self.api_key}"}

    #     response = requests.post(url, headers=headers)
    #     return response.json()

    # def get_encryption_public_key(self):
    #     url = f"{self.base_url}/tpmencryption/publickey"
    #     headers = {"Authorization": f"Bearer {self.api_key}"}

    #     response = requests.post(url, headers=headers)
    #     return response.json()
