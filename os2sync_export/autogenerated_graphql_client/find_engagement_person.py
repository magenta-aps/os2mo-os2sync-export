# Generated by ariadne-codegen on 2024-11-12 12:21
# Source: queries.graphql

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
    person: List["FindEngagementPersonEngagementsObjectsValiditiesPerson"]


class FindEngagementPersonEngagementsObjectsValiditiesPerson(BaseModel):
    uuid: UUID


FindEngagementPerson.update_forward_refs()
FindEngagementPersonEngagements.update_forward_refs()
FindEngagementPersonEngagementsObjects.update_forward_refs()
FindEngagementPersonEngagementsObjectsValidities.update_forward_refs()
FindEngagementPersonEngagementsObjectsValiditiesPerson.update_forward_refs()
