from typing import List, Optional

from odoo.addons.g2p_registry_rest_api.models import group_membership

from . import program_membership


class GroupMembersInfoIn(
    group_membership.GroupMembersInfoIn, extends=group_membership.GroupMembersInfoIn
):
    program_memberships: Optional[
        List[program_membership.RegistrantProgramMembershipIn]
    ]
