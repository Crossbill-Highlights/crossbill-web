"""Pydantic schemas for chapter prereading content API."""

from datetime import datetime

from pydantic import BaseModel


class PrereadingQuestionResponse(BaseModel):
    """Response schema for a pre-reading question/answer pair."""

    question: str
    answer: str
    user_answer: str


class PrereadingAnswerUpdate(BaseModel):
    """Schema for a single answer update."""

    question_index: int
    user_answer: str


class UpdatePrereadingAnswersRequest(BaseModel):
    """Request schema for updating prereading answers."""

    answers: list[PrereadingAnswerUpdate]


class ChapterPrereadingResponse(BaseModel):
    """Response schema for chapter prereading content."""

    id: int
    chapter_id: int
    summary: str
    keypoints: list[str]
    questions: list[PrereadingQuestionResponse]
    generated_at: datetime

    model_config = {"from_attributes": True}


class BookPrereadingResponse(BaseModel):
    """Response schema for batch prereading content for a book."""

    items: list[ChapterPrereadingResponse]
