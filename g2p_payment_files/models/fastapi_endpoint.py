from odoo import fields, models

from ..controllers.well_known import api_router


class WellknownComponent(models.Model):
    _inherit = "fastapi.endpoint"
    app: str = fields.Selection(
        selection_add=[("payment", "Payment")], ondelete={"payment": "cascade"}
    )

    def _get_fastapi_routers(self):
        if self.app == "payment":
            return [api_router]
        return super()._get_fastapi_routers()
