from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestG2PPaymentFileQRCodeConfig(TransactionCase):
    def setUp(self):
        super().setUp()
        self.QRCodeConfig = self.env["g2p.payment.file.qrcode.config"]
        self.qr_code_config = self.QRCodeConfig.create(
            {
                "name": "Test Config",
                "type": "qrcode",
                "data_type": "string",
                "body_string": "Example String",
            }
        )
        self.encryption_provider_default = self.env["g2p.encryption.provider"].create(
            {
                "name": "Test Encryption Provider",
                # "type" : "test",
            }
        )

    def test_constrains_type_and_data_type_success(self):
        try:
            self.QRCodeConfig.create(
                {
                    "name": "Barcode Config",
                    "type": "code-128-barcode",
                    "data_type": "string",
                    "body_string": "Example Barcode",
                }
            )
        except Exception as e:
            self.fail(f"Constraint check failed unexpectedly: {e}")

    def test_constrains_type_and_data_type_failure(self):
        with self.assertRaises(ValidationError):
            self.QRCodeConfig.create(
                {
                    "name": "Barcode Config",
                    "type": "code-128-barcode",
                    "data_type": "json",
                    "body_string": "{}",
                }
            )

    @patch("jose.jwt.encode")
    def test_render_data_jwt(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "mocked_jwt_token"
        result = self.qr_code_config._render_data(
            "jwt",
            '{"sample": "data"}',
            "g2p.entitlement",
            [1],
            self.encryption_provider_default,
        )
        self.assertTrue(mock_jwt_encode.called)
        self.assertIn(1, result)
        self.assertEqual(result[1], "mocked_jwt_token")

    def test_render_data_json(self):
        json_data = '{"sample": "data"}'
        result = self.qr_code_config._render_data(
            "json",
            json_data,
            "res.model",
            [1],
            self.encryption_provider_default,
        )
        self.assertEqual(len(result), 1)
        self.assertIn(1, result)
        self.assertEqual(result[1], json_data)

    def test_render_data_string(self):
        string_data = "Sample String Data"
        result = self.qr_code_config._render_data(
            "string",
            string_data,
            "res.model",
            [1],
            self.encryption_provider_default,
        )
        self.assertEqual(len(result), 1)
        self.assertIn(1, result)
        self.assertEqual(result[1], string_data)


class TestG2PPaymentFileQRCode(TransactionCase):
    def setUp(self):
        super().setUp()
        self.QRCodeModel = self.env["g2p.payment.file.qrcode"]
        self.qr_code_config = self.env["g2p.payment.file.qrcode.config"].create(
            {
                "name": "QR Config",
                "type": "qrcode",
                "data_type": "string",
                "body_string": "Test Data",
            }
        )

    @patch("qrcode.make")
    def test_generate_qrcode(self, mock_qrcode_make):
        mock_image = MagicMock()
        mock_qrcode_make.return_value = mock_image

        qr_code_record = self.QRCodeModel.create(
            {
                "qrcode_config_id": self.qr_code_config.id,
                "data": "Test Data",
            }
        )

        qr_code_record._generate_qrcode()

        self.assertTrue(mock_qrcode_make.called)
        mock_image.save.assert_called_once()

    @patch("barcode.get_barcode_class")
    def test_generate_code128_barcode(self, mock_get_barcode_class):
        mock_barcode_class = MagicMock()
        mock_get_barcode_class.return_value = mock_barcode_class

        qr_code_record = self.QRCodeModel.create(
            {
                "qrcode_config_id": self.qr_code_config.id,
                "data": "Test Data",
            }
        )

        qr_code_record._generate_code128_barcode()

    def test_compute_qrcode_content(self):
        self.qr_code_config.type = "qrcode"
        qr_code_record = self.QRCodeModel.create(
            {
                "qrcode_config_id": self.qr_code_config.id,
                "data": "Test Data",
            }
        )
        qr_code_record._compute_qrcode_content()
        self.assertTrue(qr_code_record.content_base64)
        self.assertTrue(qr_code_record.content_htmlsafe)

        self.qr_code_config.type = "code-128-barcode"
        qr_code_record = self.QRCodeModel.create(
            {
                "qrcode_config_id": self.qr_code_config.id,
                "data": "Test Data",
            }
        )
        qr_code_record._compute_qrcode_content()
        self.assertTrue(qr_code_record.content_base64)
        self.assertTrue(qr_code_record.content_htmlsafe)

    def test_get_by_name(self):
        qr_code_record = self.QRCodeModel.create(
            {
                "qrcode_config_id": self.qr_code_config.id,
                "data": "Test Data",
            }
        )

        result = qr_code_record.get_by_name("QR Config")
        self.assertEqual(result, qr_code_record)
        result = self.QRCodeModel.get_by_name("Nonexistent Name")
        self.assertIsNone(result)
