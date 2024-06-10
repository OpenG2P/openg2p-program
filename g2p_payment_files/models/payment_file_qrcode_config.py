import base64
import json
from io import BytesIO

import qrcode
import qrcode.image.svg
from barcode import Code128  # pylint: disable=[W7936]

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class G2PPaymentFileQRCodeConfig(models.Model):
    _name = "g2p.payment.file.qrcode.config"
    _description = "Payment File Config"
    _order = "id asc"

    name = fields.Char(required=True)

    type = fields.Selection(
        [
            ("qrcode", "QR code"),
            ("code-128-barcode", "Code 128 Barcode"),
        ]
    )
    data_type = fields.Selection(
        [
            ("string", "String"),
            ("json", "JSON"),
            ("jwt", "JWT"),
            # Not implemented
            # ("cwt", "CWT"),
        ]
    )

    qrcode_version = fields.Integer(default=None)
    qrcode_error_correct = fields.Selection(
        [
            ("0", "ERROR_CORRECT_M"),
            ("1", "ERROR_CORRECT_L"),
            ("2", "ERROR_CORRECT_H"),
            ("3", "ERROR_CORRECT_Q"),
        ],
        default="0",
    )
    qrcode_box_size = fields.Integer(default=10)
    qrcode_border = fields.Integer(default=4)

    body_string = fields.Char(string="Body")

    payment_config_id = fields.Many2one("g2p.payment.file.config", ondelete="cascade")

    @api.constrains("type", "data_type")
    def _constrains_type_and_data_type(self):
        if self.type.endswith("barcode") and self.data_type not in ("string",):
            raise ValidationError(
                _(f"Barcode must be of data type String. Cannot be of type {self.data_type}")
            )

    def render_datas_and_store(
        self,
        res_model,
        res_ids,
        encryption_provider,
        res_id_field_in_qrcode_model=None,
        template_engine="inline_template",
    ):
        datas = self._render_data(
            self.data_type,
            self.body_string,
            res_model,
            res_ids,
            encryption_provider,
            template_engine=template_engine,
        )
        create_vals = []
        for res_id in datas:
            val = {
                "qrcode_config_id": self.id,
                "data": datas[res_id],
            }
            if res_id_field_in_qrcode_model:
                val[res_id_field_in_qrcode_model] = res_id
            create_vals.append(val)
        QrcodeFile = self.env["g2p.payment.file.qrcode"]
        return QrcodeFile.create(create_vals)

    @api.model
    def _render_data(
        self,
        data_type,
        template_src,
        res_model,
        res_ids,
        encryption_provider,
        template_engine="inline_template",
    ):
        RenderMixin = self.env["mail.render.mixin"]
        datas = RenderMixin._render_template(
            template_src,
            res_model,
            res_ids,
            engine=template_engine,
        )
        if data_type == "string":
            pass
        elif data_type == "json":
            for res_id in res_ids:
                # the following should throw exception if not json
                json.loads(datas[res_id])
        elif data_type == "jwt":
            for res_id in res_ids:
                payload = json.loads(datas[res_id])
                datas[res_id] = encryption_provider.jwt_sign(payload)
        return datas


class G2PPaymentFileQRCode(models.TransientModel):
    _name = "g2p.payment.file.qrcode"
    _description = "Payment File QR Code"
    _order = "id desc"

    qrcode_config_id = fields.Many2one("g2p.payment.file.qrcode.config")

    data = fields.Char()

    content_base64 = fields.Char(compute="_compute_qrcode_content", store=False)
    content_htmlsafe = fields.Char(compute="_compute_qrcode_content", store=False)

    payment_batch_id = fields.Many2one("g2p.payment.batch")
    payment_id = fields.Many2one("g2p.payment")

    def _compute_qrcode_content(self):
        for rec in self:
            config = rec.qrcode_config_id
            if config.type == "code-128-barcode":
                rec._generate_code128_barcode()
            elif config.type == "qrcode":
                rec._generate_qrcode()

    def _generate_code128_barcode(self):
        self.ensure_one()
        byte_buffer = BytesIO()
        Code128(self.data).write(byte_buffer)
        byte_buffer.seek(0)
        self.content_base64 = base64.b64encode(byte_buffer.read()).decode()
        self.content_htmlsafe = "data:image/svg+xml;base64," + self.content_base64
        byte_buffer.close()

    def _generate_qrcode(self):
        self.ensure_one()
        config = self.qrcode_config_id
        img = qrcode.make(
            data=self.data,
            version=config.qrcode_version if config.qrcode_version else None,
            error_correction=int(config.qrcode_error_correct),
            box_size=config.qrcode_box_size,
            border=config.qrcode_border,
            image_factory=qrcode.image.svg.SvgPathImage,
        )
        byte_buffer = BytesIO()
        img.save(byte_buffer)
        byte_buffer.seek(0)
        self.content_base64 = base64.b64encode(byte_buffer.read()).decode()
        self.content_htmlsafe = "data:image/svg+xml;base64," + self.content_base64
        byte_buffer.close()

    def get_by_name(self, name: str):
        for rec in self:
            if rec.qrcode_config_id and rec.qrcode_config_id.name == name:
                return rec
        return None
