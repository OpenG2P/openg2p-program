from odoo.addons.component.core import AbstractComponent


class ProcessIndividualMixin(AbstractComponent):
    _inherit = "process_individual.rest.mixin"

    def _process_individual(self, individual):
        res = super()._process_individual(individual)
        if individual.dict().get("notification_preference", None):
            res["notification_preference"] = individual.notification_preference
        return res
