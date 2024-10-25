# Generated by ariadne-codegen on 2024-10-25 09:25
# Source: queries.graphql

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
    org_unit: Optional[List["FindItuserUnitOrPersonItusersObjectsValiditiesOrgUnit"]]
    person: Optional[List["FindItuserUnitOrPersonItusersObjectsValiditiesPerson"]]


class FindItuserUnitOrPersonItusersObjectsValiditiesOrgUnit(BaseModel):
    uuid: UUID


class FindItuserUnitOrPersonItusersObjectsValiditiesPerson(BaseModel):
    uuid: UUID


FindItuserUnitOrPerson.update_forward_refs()
FindItuserUnitOrPersonItusers.update_forward_refs()
FindItuserUnitOrPersonItusersObjects.update_forward_refs()
FindItuserUnitOrPersonItusersObjectsValidities.update_forward_refs()
FindItuserUnitOrPersonItusersObjectsValiditiesOrgUnit.update_forward_refs()
FindItuserUnitOrPersonItusersObjectsValiditiesPerson.update_forward_refs()
