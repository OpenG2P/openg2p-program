from unittest.mock import MagicMock

from odoo.tests.common import TransactionCase


class TestProxyMeanTestParams(TransactionCase):
    def setUp(self):
        super(TestProxyMeanTestParams, self).setUp()
        self.proxy_mean_test_params = self.env["g2p.proxy_means_test_params"]
        reg_info_model = self.env["ir.model"].search([("model", "=", "g2p.program.registrant_info")])
        self.env["ir.model.fields"].create(
            {
                "name": "x_field1",
                "ttype": "integer",
                "model": "g2p.program.registrant_info",
                "model_id": reg_info_model.id,
                "store": True,
            }
        )
        self.env["ir.model.fields"].create(
            {
                "name": "x_field2",
                "ttype": "float",
                "model": "g2p.program.registrant_info",
                "model_id": reg_info_model.id,
                "store": True,
            }
        )

    def test_get_fields_label(self):
        # Create a mock environment
        mock_env = MagicMock()

        # Mock related model and fields
        mock_reg_info = MagicMock()
        mock_env["g2p.program.registrant_info"] = mock_reg_info

        # Mock _fields attribute of mock_reg_info
        mock_reg_info._fields = {"x_field1": "Field 1", "x_field2": "Field 2"}

        # Call the get_fields_label method
        fields_labels = self.proxy_mean_test_params.get_fields_label()

        # # Assert that the mock methods were called
        # mock_reg_info._fields.items.assert_called_once()
        # mock_ir_model_obj.search.assert_called()

        # Assert the returned value
        expected_labels = [("x_field1", "x_field1"), ("x_field2", "x_field2")]
        self.assertCountEqual(fields_labels, expected_labels)
