"""Pydantic schemas for Highlight API request/response validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.schemas.book_schemas import BookCreate, TagInBook
from src.schemas.highlight_tag_schemas import HighlightTagInBook


class HighlightBase(BaseModel):
    """Base schema for Highlight."""

    text: str = Field(..., min_length=1, description="Highlighted text")
    chapter: str | None = Field(None, max_length=500, description="Chapter name")
    chapter_number: int | None = Field(None, ge=1, description="Chapter order number from TOC")
    page: int | None = Field(None, ge=0, description="Page number")
    note: str | None = Field(None, description="Note/annotation")
    datetime: str = Field(..., min_length=1, max_length=50, description="KOReader datetime format")


class HighlightCreate(HighlightBase):
    """Schema for creating a Highlight."""


class Highlight(HighlightBase):
    """Schema for Highlight response."""

    id: int
    book_id: int
    chapter_id: int | None
    highlight_tags: list[HighlightTagInBook] = Field(
        default_factory=list, description="List of highlight tags for this highlight"
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def extract_chapter_from_relationship(cls, data: Any) -> Any:
        """Extract chapter name and number from Chapter relationship object before validation."""
        # Handle both dict and ORM model object
        if isinstance(data, dict):
            # If already a dict, check if we need to transform anything
            chapter = data.get("chapter")
            if chapter is not None and hasattr(chapter, "name"):
                data["chapter"] = chapter.name
                # Also extract chapter_number if not present
                if "chapter_number" not in data or data["chapter_number"] is None:
                    data["chapter_number"] = getattr(chapter, "chapter_number", None)
        else:
            # It's an ORM model object - get attributes
            if hasattr(data, "chapter"):
                chapter = data.chapter
                if chapter is not None and hasattr(chapter, "name"):
                    # Need to set chapter to the name string
                    # Since we can't modify the ORM object, create a dict
                    data_dict = {
                        "id": data.id,
                        "book_id": data.book_id,
                        "chapter_id": data.chapter_id,
                        "text": data.text,
                        "page": data.page,
                        "note": data.note,
                        "datetime": data.datetime,
                        "created_at": data.created_at,
                        "updated_at": data.updated_at,
                        "highlight_tags": data.highlight_tags,
                        "chapter": chapter.name,
                        "chapter_number": getattr(chapter, "chapter_number", None),
                    }
                    return data_dict
        return data


class HighlightUploadRequest(BaseModel):
    """Schema for uploading highlights from KOReader."""

    book: BookCreate = Field(..., description="Book metadata")
    highlights: list[HighlightCreate] = Field(..., description="List of highlights to upload")


class HighlightUploadResponse(BaseModel):
    """Schema for highlight upload response."""

    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")
    book_id: int = Field(..., description="ID of the book")
    highlights_created: int = Field(..., ge=0, description="Number of highlights created")
    highlights_skipped: int = Field(
        ..., ge=0, description="Number of highlights skipped (duplicates)"
    )


class ChapterWithHighlights(BaseModel):
    """Schema for Chapter with its highlights."""

    id: int
    name: str
    chapter_number: int | None = Field(None, description="Chapter order number from TOC")
    highlights: list[Highlight] = Field(
        default_factory=list, description="List of highlights in this chapter"
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookDetails(BaseModel):
    """Schema for detailed Book response with chapters and highlights."""

    id: int
    title: str
    author: str | None
    isbn: str | None
    cover: str | None
    tags: list[TagInBook] = Field(default_factory=list, description="List of tags for this book")
    highlight_tags: list[HighlightTagInBook] = Field(
        default_factory=list, description="List of highlight tags for this book"
    )
    chapters: list[ChapterWithHighlights] = Field(
        default_factory=list, description="List of chapters with highlights"
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HighlightDeleteRequest(BaseModel):
    """Schema for soft deleting highlights."""

    highlight_ids: list[int] = Field(
        ..., min_length=1, description="List of highlight IDs to soft delete"
    )


class HighlightDeleteResponse(BaseModel):
    """Schema for highlight delete response."""

    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")
    deleted_count: int = Field(..., ge=0, description="Number of highlights deleted")


class HighlightSearchResult(BaseModel):
    """Schema for highlight search result with book and chapter data."""

    id: int
    text: str
    page: int | None
    note: str | None
    datetime: str
    book_id: int
    book_title: str
    book_author: str | None
    chapter_id: int | None
    chapter_name: str | None
    chapter_number: int | None = Field(None, description="Chapter order number from TOC")
    highlight_tags: list[HighlightTagInBook] = Field(
        default_factory=list, description="List of highlight tags for this highlight"
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HighlightSearchResponse(BaseModel):
    """Schema for highlight search response."""

    highlights: list[HighlightSearchResult] = Field(
        default_factory=list, description="List of matching highlights"
    )
    total: int = Field(..., ge=0, description="Total number of results")
