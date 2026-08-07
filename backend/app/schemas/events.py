from pydantic import BaseModel


class ChatEvent(BaseModel):
    type: str
    message: str