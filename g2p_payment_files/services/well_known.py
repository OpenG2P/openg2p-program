import base64
import logging

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from jose import constants, jwk

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class WellknownRestComponent(Component):
    _name = "payments_well_known.rest.service"
    _inherit = ["base.rest.service"]
    _usage = ".well-known"
    _collection = "base.rest.payment.services"
    _description = """
        Payment Well-Known API Services
    """

    @restapi.method(
        [
            (
                [
                    "/jwks.json",
                ],
                "GET",
            )
        ],
        auth="public",
    )
    def get_jwks(self):
        CryptoKeySet = self.env["g2p.crypto.key.set"].sudo()
        key_sets = CryptoKeySet.search([])
        keys_response = []
        for key_set in key_sets:
            certificate = x509.load_pem_x509_certificate(key_set.pub_cert.encode())
            cert_x5c = base64.b64encode(
                certificate.public_bytes(serialization.Encoding.DER)
            ).decode()
            pub_key = certificate.public_key()
            pub_key_jwk = jwk.RSAKey(
                algorithm=constants.ALGORITHMS.RS256,
                key=pub_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode(),
            ).to_dict()
            pub_key_jwk["kid"] = key_set.name
            # TODO: use has to come from db. For now hardcoding use: sig
            pub_key_jwk["use"] = "sig"
            pub_key_jwk["x5c"] = [cert_x5c]
            keys_response.append(pub_key_jwk)
        return {"keys": keys_response}
