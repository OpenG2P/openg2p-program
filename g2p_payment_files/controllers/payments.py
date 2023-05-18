from odoo.addons.base_rest.controllers import main


class RegistryApiController(main.RestController):
    _root_path = "/api/v1/payments/"
    _collection_name = "base.rest.payment.services"
    _default_auth = "user"
