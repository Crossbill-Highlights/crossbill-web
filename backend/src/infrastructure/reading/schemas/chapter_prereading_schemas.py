"""Pydantic schemas for chapter prereading content API."""

from datetime import datetime

from pydantic import BaseModel


class ChapterPrereadingResponse(BaseModel):
    """Response schema for chapter prereading content."""

    id: int
    chapter_id: int
    summary: str
    keypoints: list[str]
    generated_at: datetime

    model_config = {"from_attributes": True}


class BookPrereadingResponse(BaseModel):
    """Response schema for batch prereading content for a book."""

    items: list[ChapterPrereadingResponse]
