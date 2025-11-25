from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class FindItuserUnitOrPerson(BaseModel):
    itusers: "FindItuserUnitOrPersonItusers"


class FindItuserUnitOrPersonItusers(BaseModel):
    objects: List["FindItuserUnitOrPersonItusersObjects"]


class FindItuserUnitOrPersonItusersObjects(BaseModel):
    validities: List["FindItuserUnitOrPersonItusersObjectsValidities"]


class FindItuserUnitOrPersonItusersObjectsValidities(BaseModel):
    org_unit_response: Optional[
        "FindItuserUnitOrPersonItusersObjectsValiditiesOrgUnitResponse"
    ]
    person_response: Optional[
        "FindItuserUnitOrPersonItusersObjectsValiditiesPersonResponse"
    ]


class FindItuserUnitOrPersonItusersObjectsValiditiesOrgUnitResponse(BaseModel):
    uuid: UUID


class FindItuserUnitOrPersonItusersObjectsValiditiesPersonResponse(BaseModel):
    uuid: UUID


FindItuserUnitOrPerson.update_forward_refs()
FindItuserUnitOrPersonItusers.update_forward_refs()
FindItuserUnitOrPersonItusersObjects.update_forward_refs()
FindItuserUnitOrPersonItusersObjectsValidities.update_forward_refs()
FindItuserUnitOrPersonItusersObjectsValiditiesOrgUnitResponse.update_forward_refs()
FindItuserUnitOrPersonItusersObjectsValiditiesPersonResponse.update_forward_refs()
