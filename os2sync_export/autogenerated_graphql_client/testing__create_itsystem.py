from uuid import UUID

from .base_model import BaseModel


class TestingCreateItsystem(BaseModel):
    itsystem_create: "TestingCreateItsystemItsystemCreate"


class TestingCreateItsystemItsystemCreate(BaseModel):
    uuid: UUID


TestingCreateItsystem.update_forward_refs()
TestingCreateItsystemItsystemCreate.update_forward_refs()
