# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    default_auth_endpoint_url = fields.Char(
        "Authentication Endpoint URL",
        default="https://ops-bk.sandbox.fynarfin.io/oauth/token",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
    default_payment_endpoint_url = fields.Char(
        "Payment Endpoint URL",
        default="https://bulk-connector.sandbox.fynarfin.io/bulk/transfer",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
    default_status_endpoint_url = fields.Char(
        "Status Endpoint URL",
        default="https://ops-bk.sandbox.fynarfin.io/api/v1/batch",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
    default_details_endpoint_url = fields.Char(
        "Details Endpoint URL",
        default="https://ops-bk.sandbox.fynarfin.io/api/v1/batch",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )

    # Authentication parameters
    default_tenant_id = fields.Char(
        "Tenant ID",
        default="ibank-usa",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
    default_username = fields.Char(
        "Username",
        default="mifos",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
    default_password = fields.Char(
        "Password",
        default="password",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
    default_grant_type = fields.Char(
        "Grant Type",
        default="password",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
    default_authorization = fields.Char(
        "Authorization",
        default="Basic Y2xpZW50Og==",
        default_model="g2p.program.payment.manager.phee",
        required=True,
    )
