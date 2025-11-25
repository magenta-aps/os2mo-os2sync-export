from typing import List
from uuid import UUID

from .base_model import BaseModel


class FindManagerUnit(BaseModel):
    managers: "FindManagerUnitManagers"


class FindManagerUnitManagers(BaseModel):
    objects: List["FindManagerUnitManagersObjects"]


class FindManagerUnitManagersObjects(BaseModel):
    validities: List["FindManagerUnitManagersObjectsValidities"]


class FindManagerUnitManagersObjectsValidities(BaseModel):
    org_unit_response: "FindManagerUnitManagersObjectsValiditiesOrgUnitResponse"


class FindManagerUnitManagersObjectsValiditiesOrgUnitResponse(BaseModel):
    uuid: UUID


FindManagerUnit.update_forward_refs()
FindManagerUnitManagers.update_forward_refs()
FindManagerUnitManagersObjects.update_forward_refs()
FindManagerUnitManagersObjectsValidities.update_forward_refs()
FindManagerUnitManagersObjectsValiditiesOrgUnitResponse.update_forward_refs()
