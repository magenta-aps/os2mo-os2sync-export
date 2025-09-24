from uuid import UUID

from .base_model import BaseModel


class TerminateITUser(BaseModel):
    ituser_terminate: "TerminateITUserItuserTerminate"


class TerminateITUserItuserTerminate(BaseModel):
    uuid: UUID


TerminateITUser.update_forward_refs()
TerminateITUserItuserTerminate.update_forward_refs()
