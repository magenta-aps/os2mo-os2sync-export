from uuid import UUID

from .base_model import BaseModel


class TestingEmployeeCreate(BaseModel):
    employee_create: "TestingEmployeeCreateEmployeeCreate"


class TestingEmployeeCreateEmployeeCreate(BaseModel):
    uuid: UUID


TestingEmployeeCreate.update_forward_refs()
TestingEmployeeCreateEmployeeCreate.update_forward_refs()
