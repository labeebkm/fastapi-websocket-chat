from typing import Literal

from pydantic import BaseModel


class RegisterEvent(BaseModel):
    type: Literal["register"]
    username: str


class ChatEvent(BaseModel):
    type: Literal["chat"]
    username: str
    message: str


class PrivateChatEvent(BaseModel):
    type: Literal["private_chat"]
    username: str
    receiver: str
    message: str