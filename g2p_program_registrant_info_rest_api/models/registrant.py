from typing import Dict, List, Union

from odoo.addons.g2p_registry_rest_api.models import registrant


class RegistrantInfoIn(
    registrant.RegistrantInfoIn, extends=registrant.RegistrantInfoIn
):
    program_registrant_info: Union[List[Dict], Dict] = None


class RegistrantInfoOut(
    registrant.RegistrantInfoOut, extends=registrant.RegistrantInfoOut
):
    program_registrant_info: str = ""
