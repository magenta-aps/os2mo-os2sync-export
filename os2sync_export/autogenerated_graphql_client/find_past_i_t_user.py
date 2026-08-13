from datetime import datetime
from typing import List
from typing import Optional

from .base_model import BaseModel


class FindPastITUser(BaseModel):
    itusers: "FindPastITUserItusers"


class FindPastITUserItusers(BaseModel):
    objects: List["FindPastITUserItusersObjects"]


class FindPastITUserItusersObjects(BaseModel):
    validities: List["FindPastITUserItusersObjectsValidities"]


class FindPastITUserItusersObjectsValidities(BaseModel):
    user_key: str
    external_id: Optional[str]
    validity: "FindPastITUserItusersObjectsValiditiesValidity"


class FindPastITUserItusersObjectsValiditiesValidity(BaseModel):
    to: Optional[datetime]


FindPastITUser.update_forward_refs()
FindPastITUserItusers.update_forward_refs()
FindPastITUserItusersObjects.update_forward_refs()
FindPastITUserItusersObjectsValidities.update_forward_refs()
FindPastITUserItusersObjectsValiditiesValidity.update_forward_refs()
