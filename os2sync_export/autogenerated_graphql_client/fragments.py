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


AddressFields.update_forward_refs()
AddressFieldsAddressType.update_forward_refs()
AddressFieldsVisibility.update_forward_refs()
