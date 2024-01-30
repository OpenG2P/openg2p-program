# import json
# import logging

# from odoo.addons.base_rest import restapi
# from odoo.addons.component.core import Component

# _logger = logging.getLogger(__name__)


# class WellknownRestComponent(Component):
#     _name = "payments_well_known.rest.service"
#     _inherit = ["base.rest.service"]
#     _usage = ".well-known"
#     _collection = "base.rest.payment.services"
#     _description = """
#         Payment Well-Known API Services
#     """

#     @restapi.method(
#         [
#             (
#                 [
#                     "/jwks.json",
#                 ],
#                 "GET",
#             )
#         ],
#         auth="public",
#     )
#     def get_jwks(self):
#         CryptoKeySet = self.env["g2p.crypto.key.set"].sudo()
#         key_sets = CryptoKeySet.search([("status", "=", "active")])
#         jwks = [json.loads(key_set.jwk) for key_set in key_sets]
#         return {"keys": jwks}
