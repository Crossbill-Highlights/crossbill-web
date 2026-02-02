"""Pydantic schemas for Chapter API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChapterBase(BaseModel):
    """Base schema for Chapter."""

    name: str = Field(..., min_length=1, max_length=500, description="Chapter name")


class Chapter(ChapterBase):
    """Schema for Chapter response."""

    id: int
    book_id: int
    parent_id: int | None = Field(None, description="Parent chapter ID for hierarchical structure")
    chapter_number: int | None = Field(None, description="Chapter order number from TOC")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
