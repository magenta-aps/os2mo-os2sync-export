from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class AddressFields(BaseModel):
    current: Optional["AddressFieldsCurrent"]


class AddressFieldsCurrent(BaseModel):
    address_type_response: "AddressFieldsCurrentAddressTypeResponse"
    visibility_response: Optional["AddressFieldsCurrentVisibilityResponse"]
    value: str


class AddressFieldsCurrentAddressTypeResponse(BaseModel):
    uuid: UUID


class AddressFieldsCurrentVisibilityResponse(BaseModel):
    current: Optional["AddressFieldsCurrentVisibilityResponseCurrent"]


class AddressFieldsCurrentVisibilityResponseCurrent(BaseModel):
    scope: Optional[str]


class UnitFields(BaseModel):
    current: Optional["UnitFieldsCurrent"]


class UnitFieldsCurrent(BaseModel):
    uuid: UUID
    name: str
    parent_response: Optional["UnitFieldsCurrentParentResponse"]
    ancestors: List["UnitFieldsCurrentAncestors"]
    unit_type_response: Optional["UnitFieldsCurrentUnitTypeResponse"]
    unit_level_response: Optional["UnitFieldsCurrentUnitLevelResponse"]
    unit_hierarchy_response: Optional["UnitFieldsCurrentUnitHierarchyResponse"]
    addresses_response: "UnitFieldsCurrentAddressesResponse"
    itusers_response: "UnitFieldsCurrentItusersResponse"
    managers_response: "UnitFieldsCurrentManagersResponse"
    kles_response: "UnitFieldsCurrentKlesResponse"


class UnitFieldsCurrentParentResponse(BaseModel):
    current: Optional["UnitFieldsCurrentParentResponseCurrent"]


class UnitFieldsCurrentParentResponseCurrent(BaseModel):
    uuid: UUID
    itusers_response: "UnitFieldsCurrentParentResponseCurrentItusersResponse"


class UnitFieldsCurrentParentResponseCurrentItusersResponse(BaseModel):
    objects: List["UnitFieldsCurrentParentResponseCurrentItusersResponseObjects"]


class UnitFieldsCurrentParentResponseCurrentItusersResponseObjects(BaseModel):
    current: Optional[
        "UnitFieldsCurrentParentResponseCurrentItusersResponseObjectsCurrent"
    ]


class UnitFieldsCurrentParentResponseCurrentItusersResponseObjectsCurrent(BaseModel):
    user_key: str


class UnitFieldsCurrentAncestors(BaseModel):
    uuid: UUID


class UnitFieldsCurrentUnitTypeResponse(BaseModel):
    uuid: UUID


class UnitFieldsCurrentUnitLevelResponse(BaseModel):
    uuid: UUID


class UnitFieldsCurrentUnitHierarchyResponse(BaseModel):
    current: Optional["UnitFieldsCurrentUnitHierarchyResponseCurrent"]


class UnitFieldsCurrentUnitHierarchyResponseCurrent(BaseModel):
    name: str


class UnitFieldsCurrentAddressesResponse(BaseModel):
    objects: List["UnitFieldsCurrentAddressesResponseObjects"]


class UnitFieldsCurrentAddressesResponseObjects(BaseModel):
    current: Optional["UnitFieldsCurrentAddressesResponseObjectsCurrent"]


class UnitFieldsCurrentAddressesResponseObjectsCurrent(BaseModel):
    address_type_response: (
        "UnitFieldsCurrentAddressesResponseObjectsCurrentAddressTypeResponse"
    )
    name: Optional[str]


class UnitFieldsCurrentAddressesResponseObjectsCurrentAddressTypeResponse(BaseModel):
    current: Optional[
        "UnitFieldsCurrentAddressesResponseObjectsCurrentAddressTypeResponseCurrent"
    ]


class UnitFieldsCurrentAddressesResponseObjectsCurrentAddressTypeResponseCurrent(
    BaseModel
):
    scope: Optional[str]
    uuid: UUID
    user_key: str


class UnitFieldsCurrentItusersResponse(BaseModel):
    objects: List["UnitFieldsCurrentItusersResponseObjects"]


class UnitFieldsCurrentItusersResponseObjects(BaseModel):
    current: Optional["UnitFieldsCurrentItusersResponseObjectsCurrent"]


class UnitFieldsCurrentItusersResponseObjectsCurrent(BaseModel):
    user_key: str


class UnitFieldsCurrentManagersResponse(BaseModel):
    objects: List["UnitFieldsCurrentManagersResponseObjects"]


class UnitFieldsCurrentManagersResponseObjects(BaseModel):
    current: Optional["UnitFieldsCurrentManagersResponseObjectsCurrent"]


class UnitFieldsCurrentManagersResponseObjectsCurrent(BaseModel):
    person_response: Optional[
        "UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponse"
    ]


class UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponse(BaseModel):
    current: Optional[
        "UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrent"
    ]


class UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrent(BaseModel):
    itusers_response: "UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponse"


class UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponse(
    BaseModel
):
    objects: List[
        "UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponseObjects"
    ]


class UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponseObjects(
    BaseModel
):
    current: Optional[
        "UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponseObjectsCurrent"
    ]


class UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponseObjectsCurrent(
    BaseModel
):
    external_id: Optional[str]


class UnitFieldsCurrentKlesResponse(BaseModel):
    objects: List["UnitFieldsCurrentKlesResponseObjects"]


class UnitFieldsCurrentKlesResponseObjects(BaseModel):
    current: Optional["UnitFieldsCurrentKlesResponseObjectsCurrent"]


class UnitFieldsCurrentKlesResponseObjectsCurrent(BaseModel):
    kle_number_response: "UnitFieldsCurrentKlesResponseObjectsCurrentKleNumberResponse"


class UnitFieldsCurrentKlesResponseObjectsCurrentKleNumberResponse(BaseModel):
    uuid: UUID


AddressFields.update_forward_refs()
AddressFieldsCurrent.update_forward_refs()
AddressFieldsCurrentAddressTypeResponse.update_forward_refs()
AddressFieldsCurrentVisibilityResponse.update_forward_refs()
AddressFieldsCurrentVisibilityResponseCurrent.update_forward_refs()
UnitFields.update_forward_refs()
UnitFieldsCurrent.update_forward_refs()
UnitFieldsCurrentParentResponse.update_forward_refs()
UnitFieldsCurrentParentResponseCurrent.update_forward_refs()
UnitFieldsCurrentParentResponseCurrentItusersResponse.update_forward_refs()
UnitFieldsCurrentParentResponseCurrentItusersResponseObjects.update_forward_refs()
UnitFieldsCurrentParentResponseCurrentItusersResponseObjectsCurrent.update_forward_refs()
UnitFieldsCurrentAncestors.update_forward_refs()
UnitFieldsCurrentUnitTypeResponse.update_forward_refs()
UnitFieldsCurrentUnitLevelResponse.update_forward_refs()
UnitFieldsCurrentUnitHierarchyResponse.update_forward_refs()
UnitFieldsCurrentUnitHierarchyResponseCurrent.update_forward_refs()
UnitFieldsCurrentAddressesResponse.update_forward_refs()
UnitFieldsCurrentAddressesResponseObjects.update_forward_refs()
UnitFieldsCurrentAddressesResponseObjectsCurrent.update_forward_refs()
UnitFieldsCurrentAddressesResponseObjectsCurrentAddressTypeResponse.update_forward_refs()
UnitFieldsCurrentAddressesResponseObjectsCurrentAddressTypeResponseCurrent.update_forward_refs()
UnitFieldsCurrentItusersResponse.update_forward_refs()
UnitFieldsCurrentItusersResponseObjects.update_forward_refs()
UnitFieldsCurrentItusersResponseObjectsCurrent.update_forward_refs()
UnitFieldsCurrentManagersResponse.update_forward_refs()
UnitFieldsCurrentManagersResponseObjects.update_forward_refs()
UnitFieldsCurrentManagersResponseObjectsCurrent.update_forward_refs()
UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponse.update_forward_refs()
UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrent.update_forward_refs()
UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponse.update_forward_refs()
UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponseObjects.update_forward_refs()
UnitFieldsCurrentManagersResponseObjectsCurrentPersonResponseCurrentItusersResponseObjectsCurrent.update_forward_refs()
UnitFieldsCurrentKlesResponse.update_forward_refs()
UnitFieldsCurrentKlesResponseObjects.update_forward_refs()
UnitFieldsCurrentKlesResponseObjectsCurrent.update_forward_refs()
UnitFieldsCurrentKlesResponseObjectsCurrentKleNumberResponse.update_forward_refs()
