from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestWellknownComponent(TransactionCase):
    def setUp(self):
        super(TestWellknownComponent, self).setUp()
        self.endpoint_model = self.env["fastapi.endpoint"]
        self.endpoint = self.endpoint_model.create(
            {
                "app": "payment",
                "name": "test",
                "root_path": "/test",
            }
        )

    def test_get_fastapi_routers_payment_app(self):
        with patch(
            "odoo.addons.g2p_payment_files.models.fastapi_endpoint.api_router",
            autospec=True,
        ) as mock_router:
            self.endpoint._get_fastapi_routers()
