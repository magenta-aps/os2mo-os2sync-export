# Generated by ariadne-codegen on 2024-11-12 12:21
# Source: queries.graphql

from uuid import UUID

from .base_model import BaseModel


class TerminateITUser(BaseModel):
    ituser_terminate: "TerminateITUserItuserTerminate"


class TerminateITUserItuserTerminate(BaseModel):
    uuid: UUID


TerminateITUser.update_forward_refs()
TerminateITUserItuserTerminate.update_forward_refs()
