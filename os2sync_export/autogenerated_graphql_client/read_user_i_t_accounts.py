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
    fk_org_uuids: "ReadUserITAccountsPersonsObjectsCurrentFkOrgUuids"
    itusers: "ReadUserITAccountsPersonsObjectsCurrentItusers"


class ReadUserITAccountsPersonsObjectsCurrentFkOrgUuids(BaseModel):
    objects: List["ReadUserITAccountsPersonsObjectsCurrentFkOrgUuidsObjects"]


class ReadUserITAccountsPersonsObjectsCurrentFkOrgUuidsObjects(BaseModel):
    current: Optional["ReadUserITAccountsPersonsObjectsCurrentFkOrgUuidsObjectsCurrent"]


class ReadUserITAccountsPersonsObjectsCurrentFkOrgUuidsObjectsCurrent(BaseModel):
    uuid: UUID
    user_key: str
    external_id: Optional[str]


class ReadUserITAccountsPersonsObjectsCurrentItusers(BaseModel):
    objects: List["ReadUserITAccountsPersonsObjectsCurrentItusersObjects"]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjects(BaseModel):
    current: Optional["ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrent"]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrent(BaseModel):
    user_key: str
    external_id: Optional[str]
    person_response: Optional[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentPersonResponse"
    ]
    engagements_responses: "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponses"
    email: "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEmail"
    mobile: "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentMobile"
    landline: "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentLandline"


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentPersonResponse(
    BaseModel
):
    current: Optional[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentPersonResponseCurrent"
    ]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentPersonResponseCurrent(
    BaseModel
):
    cpr_number: Optional[Any]
    name: str
    nickname: str


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponses(
    BaseModel
):
    objects: List[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjects"
    ]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjects(
    BaseModel
):
    current: Optional[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrent"
    ]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrent(
    BaseModel
):
    extension_3: Optional[str]
    org_unit_response: "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentOrgUnitResponse"
    job_function_response: "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentJobFunctionResponse"


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentOrgUnitResponse(
    UnitFields
):
    pass


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentJobFunctionResponse(
    BaseModel
):
    current: Optional[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentJobFunctionResponseCurrent"
    ]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentJobFunctionResponseCurrent(
    BaseModel
):
    name: str


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEmail(BaseModel):
    objects: List[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEmailObjects"
    ]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEmailObjects(
    AddressFields
):
    pass


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentMobile(BaseModel):
    objects: List[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentMobileObjects"
    ]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentMobileObjects(
    AddressFields
):
    pass


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentLandline(BaseModel):
    objects: List[
        "ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentLandlineObjects"
    ]


class ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentLandlineObjects(
    AddressFields
):
    pass


ReadUserITAccounts.update_forward_refs()
ReadUserITAccountsPersons.update_forward_refs()
ReadUserITAccountsPersonsObjects.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrent.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentFkOrgUuids.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentFkOrgUuidsObjects.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentFkOrgUuidsObjectsCurrent.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusers.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjects.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrent.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentPersonResponse.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentPersonResponseCurrent.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponses.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjects.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrent.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentOrgUnitResponse.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentJobFunctionResponse.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEngagementsResponsesObjectsCurrentJobFunctionResponseCurrent.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEmail.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentEmailObjects.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentMobile.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentMobileObjects.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentLandline.update_forward_refs()
ReadUserITAccountsPersonsObjectsCurrentItusersObjectsCurrentLandlineObjects.update_forward_refs()
