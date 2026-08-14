from typing import Literal

from pydantic import BaseModel


class ChatEvent(BaseModel):

    type: Literal["chat"]

    message: str


class PrivateChatEvent(BaseModel):

    type: Literal["private_chat"]

    receiver: str

    message: str


class GetChatHistoryEvent(BaseModel):

    type: Literal["get_chat_history"]

    receiver: str

    before_id: int | None = None   # cursor: fetch messages older than this id

    limit: int = 4                # sliding window size, capped below