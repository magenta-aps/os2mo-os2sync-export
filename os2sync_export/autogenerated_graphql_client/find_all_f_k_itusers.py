from typing import Any
from typing import List
from typing import Optional

from .base_model import BaseModel


class FindAllFKItusers(BaseModel):
    itusers: "FindAllFKItusersItusers"


class FindAllFKItusersItusers(BaseModel):
    objects: List["FindAllFKItusersItusersObjects"]
    page_info: "FindAllFKItusersItusersPageInfo"


class FindAllFKItusersItusersObjects(BaseModel):
    current: Optional["FindAllFKItusersItusersObjectsCurrent"]


class FindAllFKItusersItusersObjectsCurrent(BaseModel):
    external_id: Optional[str]


class FindAllFKItusersItusersPageInfo(BaseModel):
    next_cursor: Optional[Any]


FindAllFKItusers.update_forward_refs()
FindAllFKItusersItusers.update_forward_refs()
FindAllFKItusersItusersObjects.update_forward_refs()
FindAllFKItusersItusersObjectsCurrent.update_forward_refs()
FindAllFKItusersItusersPageInfo.update_forward_refs()
