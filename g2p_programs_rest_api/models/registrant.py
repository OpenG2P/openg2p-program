from typing import List, Optional

from odoo.addons.g2p_registry_rest_api.models import registrant

from . import program_membership


class RegistrantProgramMemberInfoIn(
    registrant.RegistrantInfoIn, extends=registrant.RegistrantInfoIn
):
    program_memberships: Optional[
        List[program_membership.RegistrantProgramMembershipIn]
    ]


class RegistrantProgramMemberInfoOut(
    registrant.RegistrantInfoOut, extends=registrant.RegistrantInfoOut
):
    program_membership_ids: Optional[
        List[program_membership.RegistrantProgramMembershipOut]
    ]
