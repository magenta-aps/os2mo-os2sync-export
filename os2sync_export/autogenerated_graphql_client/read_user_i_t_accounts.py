from typing import Any
from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel
from .fragments import AddressFields
from .fragments import UnitFields


class ReadUserITAccounts(BaseModel):
    employees: "ReadUserITAccountsEmployees"


class ReadUserITAccountsEmployees(BaseModel):
    objects: List["ReadUserITAccountsEmployeesObjects"]


class ReadUserITAccountsEmployeesObjects(BaseModel):
    current: Optional["ReadUserITAccountsEmployeesObjectsCurrent"]


class ReadUserITAccountsEmployeesObjectsCurrent(BaseModel):
    fk_org_uuids: List["ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids"]
    itusers: List["ReadUserITAccountsEmployeesObjectsCurrentItusers"]


class ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids(BaseModel):
    uuid: UUID
    user_key: str
    external_id: Optional[str]


class ReadUserITAccountsEmployeesObjectsCurrentItusers(BaseModel):
    user_key: str
    external_id: Optional[str]
    person: Optional[List["ReadUserITAccountsEmployeesObjectsCurrentItusersPerson"]]
    engagement: Optional[
        List["ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement"]
    ]
    email: List["ReadUserITAccountsEmployeesObjectsCurrentItusersEmail"]
    mobile: List["ReadUserITAccountsEmployeesObjectsCurrentItusersMobile"]
    landline: List["ReadUserITAccountsEmployeesObjectsCurrentItusersLandline"]


class ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(BaseModel):
    cpr_number: Optional[Any]
    name: str
    nickname: str


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement(BaseModel):
    extension_3: Optional[str]
    org_unit: List["ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnit"]
    job_function: (
        "ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementJobFunction"
    )


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnit(UnitFields):
    pass


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementJobFunction(BaseModel):
    name: str


class ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(AddressFields):
    pass


class ReadUserITAccountsEmployeesObjectsCurrentItusersMobile(AddressFields):
    pass


class ReadUserITAccountsEmployeesObjectsCurrentItusersLandline(AddressFields):
    pass


ReadUserITAccounts.update_forward_refs()
ReadUserITAccountsEmployees.update_forward_refs()
ReadUserITAccountsEmployeesObjects.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrent.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusers.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersPerson.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnit.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementJobFunction.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEmail.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersMobile.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersLandline.update_forward_refs()
