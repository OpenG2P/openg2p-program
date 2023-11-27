from typing import Dict, List, Optional, Union

from odoo.addons.g2p_programs_rest_api.models import program_membership
from odoo.addons.g2p_registry_rest_api.models import naive_orm_model


class ProgramRegistrantInfoOut(naive_orm_model.NaiveOrmModel):
    state: Optional[str] = ""
    program_registrant_info: Union[Dict, List[Dict]] = {}


class ProgramMembershipIn(
    program_membership.RegistrantProgramMembershipIn,
    extends=program_membership.RegistrantProgramMembershipIn,
):
    program_registrant_info: Optional[Union[Dict, List[Dict]]] = {}


class ProgramMembershipOut(
    program_membership.RegistrantProgramMembershipOut,
    extends=program_membership.RegistrantProgramMembershipOut,
):
    program_registrant_info_ids: List[ProgramRegistrantInfoOut] = []
