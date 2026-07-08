from pydantic import BaseModel, Field


class CreateChatSessionResponse(BaseModel):
    session_id: int
    message: str


class SendChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class SendChatMessageResponse(BaseModel):
    message: str
