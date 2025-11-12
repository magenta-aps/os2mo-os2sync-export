from typing import List
from typing import Optional

from .base_model import BaseModel
from .fragments import UnitFields


class ReadOrgunit(BaseModel):
    org_units: "ReadOrgunitOrgUnits"


class ReadOrgunitOrgUnits(BaseModel):
    objects: List["ReadOrgunitOrgUnitsObjects"]


class ReadOrgunitOrgUnitsObjects(BaseModel):
    current: Optional["ReadOrgunitOrgUnitsObjectsCurrent"]


class ReadOrgunitOrgUnitsObjectsCurrent(UnitFields):
    pass


ReadOrgunit.update_forward_refs()
ReadOrgunitOrgUnits.update_forward_refs()
ReadOrgunitOrgUnitsObjects.update_forward_refs()
ReadOrgunitOrgUnitsObjectsCurrent.update_forward_refs()
