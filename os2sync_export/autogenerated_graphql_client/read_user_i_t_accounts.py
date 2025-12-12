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
    engagement_response: Optional[
        "ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponse"
    ]
    email: List["ReadUserITAccountsEmployeesObjectsCurrentItusersEmail"]
    mobile: List["ReadUserITAccountsEmployeesObjectsCurrentItusersMobile"]
    landline: List["ReadUserITAccountsEmployeesObjectsCurrentItusersLandline"]


class ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(BaseModel):
    cpr_number: Optional[Any]
    name: str
    nickname: str


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponse(BaseModel):
    current: Optional[
        "ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrent"
    ]


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrent(
    BaseModel
):
    extension_3: Optional[str]
    org_unit: List[
        "ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrentOrgUnit"
    ]
    job_function: "ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrentJobFunction"


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrentOrgUnit(
    UnitFields
):
    pass


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrentJobFunction(
    BaseModel
):
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
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponse.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrent.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrentOrgUnit.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementResponseCurrentJobFunction.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEmail.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersMobile.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersLandline.update_forward_refs()
