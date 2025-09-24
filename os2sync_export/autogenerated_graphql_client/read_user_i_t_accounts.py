from typing import Any
from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


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
    user_key: str
    external_id: Optional[str]


class ReadUserITAccountsEmployeesObjectsCurrentItusers(BaseModel):
    uuid: UUID
    user_key: str
    external_id: Optional[str]
    person: Optional[List["ReadUserITAccountsEmployeesObjectsCurrentItusersPerson"]]
    engagement: Optional[
        List["ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement"]
    ]
    email: List["ReadUserITAccountsEmployeesObjectsCurrentItusersEmail"]
    phone: List["ReadUserITAccountsEmployeesObjectsCurrentItusersPhone"]


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


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnit(BaseModel):
    uuid: UUID
    itusers: List[
        "ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnitItusers"
    ]


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnitItusers(
    BaseModel
):
    user_key: str


class ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementJobFunction(BaseModel):
    name: str


class ReadUserITAccountsEmployeesObjectsCurrentItusersEmail(BaseModel):
    address_type: "ReadUserITAccountsEmployeesObjectsCurrentItusersEmailAddressType"
    visibility: Optional[
        "ReadUserITAccountsEmployeesObjectsCurrentItusersEmailVisibility"
    ]
    value: str


class ReadUserITAccountsEmployeesObjectsCurrentItusersEmailAddressType(BaseModel):
    uuid: UUID


class ReadUserITAccountsEmployeesObjectsCurrentItusersEmailVisibility(BaseModel):
    scope: Optional[str]


class ReadUserITAccountsEmployeesObjectsCurrentItusersPhone(BaseModel):
    address_type: "ReadUserITAccountsEmployeesObjectsCurrentItusersPhoneAddressType"
    visibility: Optional[
        "ReadUserITAccountsEmployeesObjectsCurrentItusersPhoneVisibility"
    ]
    value: str


class ReadUserITAccountsEmployeesObjectsCurrentItusersPhoneAddressType(BaseModel):
    uuid: UUID


class ReadUserITAccountsEmployeesObjectsCurrentItusersPhoneVisibility(BaseModel):
    scope: Optional[str]


ReadUserITAccounts.update_forward_refs()
ReadUserITAccountsEmployees.update_forward_refs()
ReadUserITAccountsEmployeesObjects.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrent.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusers.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersPerson.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnit.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementOrgUnitItusers.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEngagementJobFunction.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEmail.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEmailAddressType.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersEmailVisibility.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersPhone.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersPhoneAddressType.update_forward_refs()
ReadUserITAccountsEmployeesObjectsCurrentItusersPhoneVisibility.update_forward_refs()
