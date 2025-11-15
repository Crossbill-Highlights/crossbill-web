"""Pydantic schemas for HighlightTag API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class HighlightTagBase(BaseModel):
    """Base schema for HighlightTag."""

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")


class HighlightTag(HighlightTagBase):
    """Schema for HighlightTag response."""

    id: int
    book_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HighlightTagInBook(BaseModel):
    """Minimal highlight tag schema for book responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class HighlightTagCreateRequest(BaseModel):
    """Schema for creating a new highlight tag."""

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")


class HighlightTagsResponse(BaseModel):
    """Schema for list of highlight tags response."""

    tags: list[HighlightTag] = Field(default_factory=list, description="List of highlight tags")


class HighlightTagAssociationRequest(BaseModel):
    """Schema for associating a tag with a highlight."""

    tag_id: int | None = Field(None, description="ID of existing tag to associate")
    name: str | None = Field(
        None, min_length=1, max_length=100, description="Name of tag to create/associate"
    )
