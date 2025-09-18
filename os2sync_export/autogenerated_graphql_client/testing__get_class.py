from typing import List
from uuid import UUID

from .base_model import BaseModel


class TestingGetClass(BaseModel):
    classes: "TestingGetClassClasses"


class TestingGetClassClasses(BaseModel):
    objects: List["TestingGetClassClassesObjects"]


class TestingGetClassClassesObjects(BaseModel):
    uuid: UUID


TestingGetClass.update_forward_refs()
TestingGetClassClasses.update_forward_refs()
TestingGetClassClassesObjects.update_forward_refs()
