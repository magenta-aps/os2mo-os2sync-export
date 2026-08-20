from uuid import UUID

from .base_model import BaseModel


class TestingCreateClass(BaseModel):
    class_create: "TestingCreateClassClassCreate"


class TestingCreateClassClassCreate(BaseModel):
    uuid: UUID


TestingCreateClass.update_forward_refs()
TestingCreateClassClassCreate.update_forward_refs()
