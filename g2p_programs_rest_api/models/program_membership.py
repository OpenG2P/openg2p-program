from datetime import date

from odoo.addons.g2p_registry_rest_api.models import naive_orm_model


class RegistrantProgramMembershipIn(naive_orm_model.NaiveOrmModel):
    name: str = None
    enrollment_date: date = None


class RegistrantProgramMembershipOut(naive_orm_model.NaiveOrmModel):
    program_id: int = None
    state: str = None
    enrollment_date: date = None
    exit_date: date = None
