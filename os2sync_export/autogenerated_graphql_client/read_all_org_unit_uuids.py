from typing import List
from uuid import UUID

from .base_model import BaseModel


class ReadAllOrgUnitUuids(BaseModel):
    org_units: "ReadAllOrgUnitUuidsOrgUnits"


class ReadAllOrgUnitUuidsOrgUnits(BaseModel):
    objects: List["ReadAllOrgUnitUuidsOrgUnitsObjects"]


class ReadAllOrgUnitUuidsOrgUnitsObjects(BaseModel):
    uuid: UUID


ReadAllOrgUnitUuids.update_forward_refs()
ReadAllOrgUnitUuidsOrgUnits.update_forward_refs()
ReadAllOrgUnitUuidsOrgUnitsObjects.update_forward_refs()
