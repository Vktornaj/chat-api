from pydantic import BaseModel
from datetime import datetime


class MessageSend(BaseModel):
    sender: str
    receiver: str
    body: str


class MessageCreate(BaseModel):
    owner_id: int
    receiver_id: int
    body: str
    date: datetime
    state: str
