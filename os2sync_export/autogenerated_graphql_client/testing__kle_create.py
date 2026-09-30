from uuid import UUID

from .base_model import BaseModel


class TestingKleCreate(BaseModel):
    kle_create: "TestingKleCreateKleCreate"


class TestingKleCreateKleCreate(BaseModel):
    uuid: UUID


TestingKleCreate.update_forward_refs()
TestingKleCreateKleCreate.update_forward_refs()
