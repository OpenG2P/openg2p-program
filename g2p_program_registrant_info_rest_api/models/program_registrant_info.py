from datetime import datetime
from odoo.addons.g2p_programs_rest_api.models import program_membership
from odoo.addons.g2p_registry_rest_api.models import naive_orm_model


class ProgramRegistrantInfoOut(naive_orm_model.NaiveOrmModel):
    state: str | None = ""
    program_registrant_info: dict | list | None = None
    create_date: datetime


class ProgramMembershipIn(
    program_membership.RegistrantProgramMembershipIn,
    extends=program_membership.RegistrantProgramMembershipIn,
):
    program_registrant_info: dict | list | None = None


class ProgramMembershipOut(
    program_membership.RegistrantProgramMembershipOut,
    extends=program_membership.RegistrantProgramMembershipOut,
):
    program_registrant_info_ids: list[ProgramRegistrantInfoOut] = []
