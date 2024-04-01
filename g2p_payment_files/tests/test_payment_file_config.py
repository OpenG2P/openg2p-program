import base64
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from odoo.addons.mail.models.mail_template import MailTemplate


class TestG2PPaymentFileConfig(TransactionCase):
    def setUp(self):
        super(TestG2PPaymentFileConfig, self).setUp()
        self.document_store = MagicMock()
        self.document_store.add_file.side_effect = self.mock_add_file
        self.payment_file_config = self.env["g2p.payment.file.config"].create(
            {
                "name": "Test Payment File Config",
                "type": "pdf",
                "body_string": "<p>Sample Body</p>",
            }
        )
        MailTemplate._render_template = MagicMock(
            return_value={1: "<p>Rendered HTML</p>"}
        )

    def mock_add_file(self, file_content, extension):
        return {
            "name": "Mocked File" + extension,
            "content": base64.b64encode(file_content),
        }

    @patch("pdfkit.from_string")
    def test_render_and_store_pdf(self, mock_pdfkit):
        mock_pdfkit.return_value = b"PDF Content"
        document_files = self.payment_file_config.render_and_store(
            "g2p.entitlement", [1], self.document_store
        )
        self.assertEqual(len(document_files), 1)
        self.assertIn(".pdf", document_files[0]["name"])
        self.assertIn(
            "PDF Content",
            base64.b64decode(document_files[0]["content"]).decode("utf-8"),
        )
        mock_pdfkit.assert_called_once()

    def test_render_and_store_csv(self):
        self.payment_file_config.type = "csv"
        document_files = self.payment_file_config.render_and_store(
            "g2p.entitlement", [1], self.document_store
        )
        self.assertEqual(len(document_files), 1)
        self.assertIn(".csv", document_files[0]["name"])
        self.assertIn(
            "Sample Body",
            base64.b64decode(document_files[0]["content"]).decode("utf-8"),
        )

    @patch("odoo.addons.mail.models.mail_template.MailTemplate._render_template")
    def test_render_html(self, mock_render_template):
        mock_render_template.return_value = {1: "<p>Rendered HTML</p>"}
        result = self.payment_file_config.render_html("res.model", 1)
        self.assertEqual(result, "<p>Rendered HTML</p>")
        mock_render_template.assert_called_once()
