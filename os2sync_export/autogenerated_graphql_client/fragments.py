from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class AddressFields(BaseModel):
    address_type: "AddressFieldsAddressType"
    visibility: Optional["AddressFieldsVisibility"]
    value: str


class AddressFieldsAddressType(BaseModel):
    uuid: UUID


class AddressFieldsVisibility(BaseModel):
    scope: Optional[str]


class UnitFields(BaseModel):
    uuid: UUID
    name: str
    parent: Optional["UnitFieldsParent"]
    ancestors: List["UnitFieldsAncestors"]
    unit_type: Optional["UnitFieldsUnitType"]
    org_unit_level: Optional["UnitFieldsOrgUnitLevel"]
    org_unit_hierarchy_model: Optional["UnitFieldsOrgUnitHierarchyModel"]
    addresses: List["UnitFieldsAddresses"]
    itusers: List["UnitFieldsItusers"]
    managers: List["UnitFieldsManagers"]
    kles: List["UnitFieldsKles"]


class UnitFieldsParent(BaseModel):
    uuid: UUID
    itusers: List["UnitFieldsParentItusers"]


class UnitFieldsParentItusers(BaseModel):
    user_key: str


class UnitFieldsAncestors(BaseModel):
    uuid: UUID


class UnitFieldsUnitType(BaseModel):
    uuid: UUID


class UnitFieldsOrgUnitLevel(BaseModel):
    uuid: UUID


class UnitFieldsOrgUnitHierarchyModel(BaseModel):
    name: str


class UnitFieldsAddresses(BaseModel):
    address_type: "UnitFieldsAddressesAddressType"
    name: Optional[str]


class UnitFieldsAddressesAddressType(BaseModel):
    scope: Optional[str]
    uuid: UUID
    user_key: str


class UnitFieldsItusers(BaseModel):
    user_key: str


class UnitFieldsManagers(BaseModel):
    person: Optional[List["UnitFieldsManagersPerson"]]


class UnitFieldsManagersPerson(BaseModel):
    itusers: List["UnitFieldsManagersPersonItusers"]


class UnitFieldsManagersPersonItusers(BaseModel):
    external_id: Optional[str]


class UnitFieldsKles(BaseModel):
    kle_number: List["UnitFieldsKlesKleNumber"]


class UnitFieldsKlesKleNumber(BaseModel):
    uuid: UUID


AddressFields.update_forward_refs()
AddressFieldsAddressType.update_forward_refs()
AddressFieldsVisibility.update_forward_refs()
UnitFields.update_forward_refs()
UnitFieldsParent.update_forward_refs()
UnitFieldsParentItusers.update_forward_refs()
UnitFieldsAncestors.update_forward_refs()
UnitFieldsUnitType.update_forward_refs()
UnitFieldsOrgUnitLevel.update_forward_refs()
UnitFieldsOrgUnitHierarchyModel.update_forward_refs()
UnitFieldsAddresses.update_forward_refs()
UnitFieldsAddressesAddressType.update_forward_refs()
UnitFieldsItusers.update_forward_refs()
UnitFieldsManagers.update_forward_refs()
UnitFieldsManagersPerson.update_forward_refs()
UnitFieldsManagersPersonItusers.update_forward_refs()
UnitFieldsKles.update_forward_refs()
UnitFieldsKlesKleNumber.update_forward_refs()
