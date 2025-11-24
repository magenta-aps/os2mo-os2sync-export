from typing import Any
from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel
from .fragments import AddressFields
from .fragments import UnitFields


class ReadUserITAccounts(BaseModel):
    persons: "ReadUserITAccountsPersons"


class ReadUserITAccountsPersons(BaseModel):
    objects: List["ReadUserITAccountsPersonsObjects"]


class ReadUserITAccountsPersonsObjects(BaseModel):
    current: Optional["ReadUserITAccountsPersonsObjectsCurrent"]


class ReadUserITAccountsPersonsObjectsCurrent(BaseModel):
    fk_org_uuids: List["ReadUserITAccountsPersonsObjectsCurrentFkOrgUuids"]
    itusers: List["ReadUserITAccountsPersonsObjectsCurrentItusers"]


class ReadUserITAccountsPersonsObjectsCurrentFkOrgUuids(BaseModel):
    uuid: UUID
    user_key: str
    external_id: Optional[str]


class ReadUserITAccountsPersonsObjectsCurrentItusers(BaseModel):
    user_key: str
    external_id: Optional[str]
    person: Optional[List["ReadUserITAccountsPersonsObjectsCurrentItusersPerson"]]
    engagement: Optional[
        List["ReadUserITAccountsPersonsObjectsCurrentItusersEngagement"]
    ]
    email: List["ReadUserITAccountsPersonsObjectsCurrentItusersEmail"]
    mobile: List["ReadUserITAccountsPersonsObjectsCurrentItusersMobile"]
    landline: List["ReadUserITAccountsPersonsObjectsCurrentItusersLandline"]


class ReadUserITAccountsPersonsObjectsCurrentItusersPerson(BaseModel):
    cpr_number: Optional[Any]
    name: str
    nickname: str


class ReadUserITAccountsPersonsObjectsCurrentItusersEngagement(BaseModel):
    extension_3: Optional[str]
    org_unit: List["ReadUserITAccountsPersonsObjectsCurrentItusersEngagementOrgUnit"]
    job_function: "ReadUserITAccountsPersonsObjectsCurrentItusersEngagementJobFunction"


class ReadUserITAccountsPersonsObjectsCurrentItusersEngagementOrgUnit(UnitFields):
    pass


class ReadUserITAccountsPersonsObjectsCurrentItusersEngagementJobFunction(BaseModel):
    name: str


class ReadUserITAccountsPersonsObjectsCurrentItusersEmail(AddressFields):
    pass


class ReadUserITAccountsPersonsObjectsCurrentItusersMobile(AddressFields):
    pass


class ReadUserITAccountsPersonsObjectsCurrentItusersLandline(AddressFields):
    pass


ReadUserITAccounts.update_forward_refs()
ReadUserITAccountsPersons.update_forward_refs()
ReadUserITAccountsPersonsObjects.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrent.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentFkOrgUuids.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusers.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersPerson.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersEngagement.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersEngagementOrgUnit.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersEngagementJobFunction.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersEmail.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersMobile.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersLandline.update_forward_refs()
