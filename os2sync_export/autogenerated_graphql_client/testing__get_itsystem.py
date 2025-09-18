from typing import List
from uuid import UUID

from .base_model import BaseModel


class TestingGetItsystem(BaseModel):
    itsystems: "TestingGetItsystemItsystems"


class TestingGetItsystemItsystems(BaseModel):
    objects: List["TestingGetItsystemItsystemsObjects"]


class TestingGetItsystemItsystemsObjects(BaseModel):
    uuid: UUID


TestingGetItsystem.update_forward_refs()
TestingGetItsystemItsystems.update_forward_refs()
TestingGetItsystemItsystemsObjects.update_forward_refs()
