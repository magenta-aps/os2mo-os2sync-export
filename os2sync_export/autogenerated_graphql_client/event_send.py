from .base_model import BaseModel


class EventSend(BaseModel):
    event_send: bool


EventSend.update_forward_refs()
