from typing import List
from uuid import UUID

from .base_model import BaseModel


class ReadAllEmployeeUuids(BaseModel):
    employees: "ReadAllEmployeeUuidsEmployees"


class ReadAllEmployeeUuidsEmployees(BaseModel):
    objects: List["ReadAllEmployeeUuidsEmployeesObjects"]


class ReadAllEmployeeUuidsEmployeesObjects(BaseModel):
    uuid: UUID


ReadAllEmployeeUuids.update_forward_refs()
ReadAllEmployeeUuidsEmployees.update_forward_refs()
ReadAllEmployeeUuidsEmployeesObjects.update_forward_refs()
