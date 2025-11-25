from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class FindAddressUnitOrPerson(BaseModel):
    addresses: "FindAddressUnitOrPersonAddresses"


class FindAddressUnitOrPersonAddresses(BaseModel):
    objects: List["FindAddressUnitOrPersonAddressesObjects"]


class FindAddressUnitOrPersonAddressesObjects(BaseModel):
    validities: List["FindAddressUnitOrPersonAddressesObjectsValidities"]


class FindAddressUnitOrPersonAddressesObjectsValidities(BaseModel):
    org_unit_response: Optional[
        "FindAddressUnitOrPersonAddressesObjectsValiditiesOrgUnitResponse"
    ]
    person_response: Optional[
        "FindAddressUnitOrPersonAddressesObjectsValiditiesPersonResponse"
    ]


class FindAddressUnitOrPersonAddressesObjectsValiditiesOrgUnitResponse(BaseModel):
    uuid: UUID


class FindAddressUnitOrPersonAddressesObjectsValiditiesPersonResponse(BaseModel):
    uuid: UUID


FindAddressUnitOrPerson.update_forward_refs()
FindAddressUnitOrPersonAddresses.update_forward_refs()
FindAddressUnitOrPersonAddressesObjects.update_forward_refs()
FindAddressUnitOrPersonAddressesObjectsValidities.update_forward_refs()
FindAddressUnitOrPersonAddressesObjectsValiditiesOrgUnitResponse.update_forward_refs()
FindAddressUnitOrPersonAddressesObjectsValiditiesPersonResponse.update_forward_refs()
