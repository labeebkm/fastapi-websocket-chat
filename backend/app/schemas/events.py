from typing import Literal

from pydantic import BaseModel


class ChatEvent(BaseModel):

    type: Literal["chat"]

    message: str


class PrivateChatEvent(BaseModel):

    type: Literal["private_chat"]

    receiver: str

    message: str