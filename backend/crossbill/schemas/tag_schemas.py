"""Pydantic schemas for Tag API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base schema for Tag."""

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")


class Tag(TagBase):
    """Schema for Tag response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookUpdateRequest(BaseModel):
    """Schema for updating a book."""

    tags: list[str] = Field(default_factory=list, description="List of tag names")
