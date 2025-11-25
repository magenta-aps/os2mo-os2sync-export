from typing import List
from uuid import UUID

from .base_model import BaseModel


class FindEngagementPerson(BaseModel):
    engagements: "FindEngagementPersonEngagements"


class FindEngagementPersonEngagements(BaseModel):
    objects: List["FindEngagementPersonEngagementsObjects"]


class FindEngagementPersonEngagementsObjects(BaseModel):
    validities: List["FindEngagementPersonEngagementsObjectsValidities"]


class FindEngagementPersonEngagementsObjectsValidities(BaseModel):
    person_response: "FindEngagementPersonEngagementsObjectsValiditiesPersonResponse"


class FindEngagementPersonEngagementsObjectsValiditiesPersonResponse(BaseModel):
    uuid: UUID


FindEngagementPerson.update_forward_refs()
FindEngagementPersonEngagements.update_forward_refs()
FindEngagementPersonEngagementsObjects.update_forward_refs()
FindEngagementPersonEngagementsObjectsValidities.update_forward_refs()
FindEngagementPersonEngagementsObjectsValiditiesPersonResponse.update_forward_refs()
