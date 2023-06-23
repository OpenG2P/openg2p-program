import pdfkit

from odoo import fields, models


class G2PPaymentFileConfig(models.Model):
    _name = "g2p.payment.file.config"
    _description = "Payment File Config"
    _order = "id desc"

    name = fields.Char()

    type = fields.Selection(
        [
            ("pdf", "PDF"),
            ("csv", "CSV"),
        ],
        default="pdf",
    )

    # body_html = fields.Html(
    #     compute="_compute_html_preview",
    #     store=False,
    #     translate=False,
    #     sanitize=False,
    # )
    body_string = fields.Text(string="Body")

    qrcode_config_ids = fields.One2many(
        "g2p.payment.file.qrcode.config", "payment_config_id"
    )

    # def _compute_html_preview(self):
    #     for rec in self:
    #         rec.body_html = rec.body_string

    def render_and_store(self, res_model, res_ids, document_store):
        document_files = []
        for res_id in res_ids:
            document_files.append(
                document_store.add_file(
                    self.render_template(res_model, res_id), extension="." + self.type
                )
            )
        return document_files

    def render_template(self, res_model, res_id):
        if self.type == "pdf":
            return self.render_pdf(res_model, res_id)
        elif self.type == "csv":
            return self.render_csv(res_model, res_id)

    def render_html(self, res_model, res_id):
        RenderMixin = self.env["mail.render.mixin"]
        template_src = self.body_string
        data = RenderMixin._render_template(
            template_src,
            res_model,
            [
                res_id,
            ],
            engine="qweb",
        )
        # This render_template is removing <html> and <head> content.
        return data[res_id]

    def render_pdf(self, res_model, res_id):
        res = self.render_html(res_model, res_id)
        return pdfkit.from_string(res)

    def render_csv(self, res_model, res_id):
        return bytes(self.render_html(res_model, res_id), "utf-8")
