from odoo.addons.g2p_registry_rest_api.models import registrant

from . import program_membership


class RegistrantProgramMemberInfoIn(registrant.RegistrantInfoIn, extends=registrant.RegistrantInfoIn):
    program_memberships: list[program_membership.RegistrantProgramMembershipIn] | None


class RegistrantProgramMemberInfoOut(registrant.RegistrantInfoOut, extends=registrant.RegistrantInfoOut):
    program_membership_ids: list[program_membership.RegistrantProgramMembershipOut] | None
