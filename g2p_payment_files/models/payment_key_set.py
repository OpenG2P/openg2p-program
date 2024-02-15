import base64
import json
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from jose import constants, jwk  # pylint: disable=[W7936]

from odoo import api, fields, models


class G2PCryptoKeySet(models.Model):
    _name = "g2p.crypto.key.set"
    _description = "G2P Crypto Key Set"
    _order = "id desc"

    name = fields.Char(string="kid", required=True)

    type = fields.Selection(
        [
            ("rsa", "RSA"),
        ],
        default="rsa",
    )

    size = fields.Selection(
        [
            ("2048", "2048"),
            ("3072", "3072"),
            ("4096", "4096"),
        ],
        default="2048",
    )

    priv_key = fields.Char(compute="_compute_priv_key", store=True)
    pub_cert = fields.Char(compute="_compute_pub_cert", store=True)

    jwk = fields.Char(compute="_compute_jwk", store=True)

    use = fields.Selection(
        [
            ("sig", "Signature"),
            ("enc", "Encryption"),
        ],
        default="sig",
    )
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
        return super().create(values)

    @api.depends("type", "size")
    def _compute_priv_key(self):
        for rec in self:
            if rec.type == "rsa":
                priv_key = rsa.generate_private_key(65537, int(rec.size))
                rec.priv_key = priv_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    # Hardcoding no encryption for now
                    encryption_algorithm=serialization.NoEncryption(),
                ).decode()
            else:
                rec.priv_key = None

    @api.depends("priv_key")
    def _compute_pub_cert(self):
        web_base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        web_base_hostname = urlparse(web_base_url).netloc
        for rec in self:
            if rec.type == "rsa":
                priv_key = serialization.load_pem_private_key(
                    data=rec.priv_key.encode(),
                    password=None,
                )
                pub_key = priv_key.public_key()
                sub_name = x509.Name(
                    [x509.NameAttribute(NameOID.COMMON_NAME, web_base_hostname)]
                )
                alt_names = [x509.DNSName(web_base_hostname)]
                san = x509.SubjectAlternativeName(alt_names)

                utcnow = datetime.utcnow()
                # No signer as of now.
                # TODO: Add a common signer cert for openg2p,
                # which signs every newly created cert.
                # (Probably a oca/vault based implementation)
                cert = (
                    x509.CertificateBuilder()
                    .subject_name(sub_name)
                    .issuer_name(sub_name)
                    .public_key(pub_key)
                    .serial_number(1000)
                    .not_valid_before(utcnow)
                    .not_valid_after(utcnow + timedelta(days=10 * 365))
                    .add_extension(san, False)
                    .sign(priv_key, hashes.SHA256())
                )
                rec.pub_cert = cert.public_bytes(encoding=serialization.Encoding.PEM)
            else:
                rec.pub_cert = None

    @api.depends("pub_cert", "use")
    def _compute_jwk(self):
        for key_set in self:
            certificate = x509.load_pem_x509_certificate(key_set.pub_cert.encode())
            cert_x5c = base64.b64encode(
                certificate.public_bytes(serialization.Encoding.DER)
            ).decode()
            pub_key = certificate.public_key()
            # TODO: For now hardcoding alogrithm
            pub_key_jwk = jwk.RSAKey(
                algorithm=constants.ALGORITHMS.RS256,
                key=pub_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode(),
            ).to_dict()
            pub_key_jwk["kid"] = key_set.name
            pub_key_jwk["use"] = key_set.use
            pub_key_jwk["x5c"] = [cert_x5c]
            key_set.jwk = json.dumps(pub_key_jwk)
