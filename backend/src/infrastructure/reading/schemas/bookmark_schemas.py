"""Pydantic schemas for Bookmark API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class BookmarkBase(BaseModel):
    """Base schema for Bookmark."""

    highlight_id: int = Field(..., description="ID of the highlight to bookmark")


class Bookmark(BookmarkBase):
    """Schema for Bookmark response."""

    id: int
    book_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BookmarkCreateRequest(BaseModel):
    """Schema for creating a new bookmark."""

    highlight_id: int = Field(..., description="ID of the highlight to bookmark")


class BookmarksResponse(BaseModel):
    """Schema for list of bookmarks response."""

    bookmarks: list[Bookmark] = Field(..., description="List of bookmarks")
