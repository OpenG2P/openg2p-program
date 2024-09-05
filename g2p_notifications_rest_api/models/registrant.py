from odoo.addons.g2p_registry_rest_api.models import registrant


class RegistrantProgramMemberInfoIn(registrant.RegistrantInfoIn, extends=registrant.RegistrantInfoIn):
    notification_preference: str = "none"


class RegistrantProgramMemberInfoOut(registrant.RegistrantInfoOut, extends=registrant.RegistrantInfoOut):
    notification_preference: str = "none"
