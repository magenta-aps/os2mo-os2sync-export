from uuid import UUID

from .base_model import BaseModel


class TestingItsystemTerminate(BaseModel):
    itsystem_terminate: "TestingItsystemTerminateItsystemTerminate"


class TestingItsystemTerminateItsystemTerminate(BaseModel):
    uuid: UUID


TestingItsystemTerminate.update_forward_refs()
TestingItsystemTerminateItsystemTerminate.update_forward_refs()
