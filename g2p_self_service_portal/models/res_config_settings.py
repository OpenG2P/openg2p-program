from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = ["res.config.settings"]

    self_service_logo = fields.Many2one(
        "ir.attachment",
        config_parameter="g2p_self_service_portal.self_service_logo_attachment",
    )

    self_service_signup_id_type = fields.Many2one(
        "g2p.id.type",
        config_parameter="g2p_self_service_portal.self_service_signup_id_type",
    )

    # For now this is a list of references. Example:
    # [
    #   'g2p.program.notification.manager.sms,2',
    #   'g2p.program.notification.manager.fast2sms,4',
    #   'g2p.program.notification.manager.email,14'
    # ]
    self_service_otp_notification_managers = fields.Char(
        config_parameter="g2p_self_service_portal.otp_notification_managers"
    )
