from uuid import UUID

from .base_model import BaseModel


class TestingOrgUnitTerminate(BaseModel):
    org_unit_terminate: "TestingOrgUnitTerminateOrgUnitTerminate"


class TestingOrgUnitTerminateOrgUnitTerminate(BaseModel):
    uuid: UUID


TestingOrgUnitTerminate.update_forward_refs()
TestingOrgUnitTerminateOrgUnitTerminate.update_forward_refs()
