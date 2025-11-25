from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class FindKLEUnit(BaseModel):
    itusers: "FindKLEUnitItusers"


class FindKLEUnitItusers(BaseModel):
    objects: List["FindKLEUnitItusersObjects"]


class FindKLEUnitItusersObjects(BaseModel):
    validities: List["FindKLEUnitItusersObjectsValidities"]


class FindKLEUnitItusersObjectsValidities(BaseModel):
    org_unit_response: Optional["FindKLEUnitItusersObjectsValiditiesOrgUnitResponse"]


class FindKLEUnitItusersObjectsValiditiesOrgUnitResponse(BaseModel):
    uuid: UUID


FindKLEUnit.update_forward_refs()
FindKLEUnitItusers.update_forward_refs()
FindKLEUnitItusersObjects.update_forward_refs()
FindKLEUnitItusersObjectsValidities.update_forward_refs()
FindKLEUnitItusersObjectsValiditiesOrgUnitResponse.update_forward_refs()
