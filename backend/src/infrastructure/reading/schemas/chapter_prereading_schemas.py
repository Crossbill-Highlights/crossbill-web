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


class EreaderChapterPrereadingItem(BaseModel):
    """Ereader-friendly prereading content for a single chapter.

    Questions are exposed as plain strings only (no AI or user answers) to keep
    the device payload small and preserve active-recall value.
    """

    chapter_id: int
    chapter_name: str
    chapter_number: int | None
    parent_chapter_name: str | None
    summary: str
    keypoints: list[str]
    questions: list[str]
    generated_at: datetime
