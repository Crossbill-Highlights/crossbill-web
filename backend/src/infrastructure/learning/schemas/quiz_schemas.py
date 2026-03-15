from pydantic import BaseModel, Field


class CreateQuizSessionResponse(BaseModel):
    session_id: int
    message: str


class SendQuizMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class SendQuizMessageResponse(BaseModel):
    message: str
