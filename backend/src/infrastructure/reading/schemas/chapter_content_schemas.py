"""Schemas for chapter content API responses."""

from pydantic import BaseModel, Field


class ChapterContentResponse(BaseModel):
    """Response schema for chapter text content."""

    chapter_id: int = Field(..., description="ID of the chapter")
    chapter_name: str = Field(..., description="Name of the chapter")
    book_id: int = Field(..., description="ID of the book")
    content: str = Field(..., description="Full text content of the chapter")
