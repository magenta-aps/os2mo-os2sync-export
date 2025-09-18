from typing import List
from uuid import UUID

from .base_model import BaseModel


class FindFKItsystem(BaseModel):
    itsystems: "FindFKItsystemItsystems"


class FindFKItsystemItsystems(BaseModel):
    objects: List["FindFKItsystemItsystemsObjects"]


class FindFKItsystemItsystemsObjects(BaseModel):
    uuid: UUID


FindFKItsystem.update_forward_refs()
FindFKItsystemItsystems.update_forward_refs()
FindFKItsystemItsystemsObjects.update_forward_refs()
