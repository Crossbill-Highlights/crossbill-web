"""Pydantic schemas for Highlight API request/response validation."""

from datetime import datetime as dt
from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.schemas.book_schemas import BookCreate, TagInBook
from src.schemas.bookmark_schemas import Bookmark
from src.schemas.flashcard_schemas import Flashcard
from src.schemas.highlight_tag_schemas import (
    HighlightTagGroupInBook,
    HighlightTagInBook,
)


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


class HighlightResponseBase(HighlightBase):
    """Base schema for Highlight response (without flashcards).

    Use this when you need highlight data but don't want nested flashcards.
    """

    id: int
    book_id: int
    chapter_id: int | None
    highlight_tags: list[HighlightTagInBook] = Field(
        default_factory=list, description="List of highlight tags for this highlight"
    )
    created_at: dt
    updated_at: dt

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def extract_chapter_from_relationship(cls, data: Any) -> Any:  # noqa: ANN401
        """Extract chapter name and number from Chapter relationship object before validation.

        This validator dynamically uses cls.model_fields, so it works correctly
        for both this base class and any subclasses that add additional fields.
        """
        # Handle dict input
        if isinstance(data, dict):
            chapter = data.get("chapter")
            if chapter is not None and hasattr(chapter, "name"):
                data["chapter"] = chapter.name
                if "chapter_number" not in data or data["chapter_number"] is None:
                    data["chapter_number"] = getattr(chapter, "chapter_number", None)
            return data

        # Handle ORM model object - convert to dict using cls.model_fields
        if hasattr(data, "chapter"):
            chapter = data.chapter
            result: dict[str, Any] = {}

            for field_name in cls.model_fields:
                if field_name == "chapter":
                    result["chapter"] = (
                        chapter.name if chapter and hasattr(chapter, "name") else None
                    )
                elif field_name == "chapter_number":
                    result["chapter_number"] = (
                        getattr(chapter, "chapter_number", None) if chapter else None
                    )
                elif hasattr(data, field_name):
                    value = getattr(data, field_name)
                    # Convert SQLAlchemy collections to lists
                    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
                        try:
                            result[field_name] = list(value)
                        except TypeError:
                            result[field_name] = value
                    else:
                        result[field_name] = value

            return result

        return data


class Highlight(HighlightResponseBase):
    """Schema for Highlight response with flashcards."""

    flashcards: list[Flashcard] = Field(
        default_factory=list, description="List of flashcards for this highlight"
    )


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
    created_at: dt
    updated_at: dt

    model_config = {"from_attributes": True}


class BookDetails(BaseModel):
    """Schema for detailed Book response with chapters and highlights."""

    id: int
    title: str
    author: str | None
    isbn: str | None
    cover: str | None
    description: str | None = None
    language: str | None = None
    page_count: int | None = None
    tags: list[TagInBook] = Field(default_factory=list, description="List of tags for this book")
    highlight_tags: list[HighlightTagInBook] = Field(
        default_factory=list, description="List of highlight tags for this book"
    )
    highlight_tag_groups: list[HighlightTagGroupInBook] = Field(
        default_factory=list, description="List of highlight tag groups for this book"
    )
    bookmarks: list[Bookmark] = Field(
        default_factory=list, description="List of bookmarks for this book"
    )
    chapters: list[ChapterWithHighlights] = Field(
        default_factory=list, description="List of chapters with highlights"
    )
    created_at: dt
    updated_at: dt
    last_viewed: dt | None = None

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
    created_at: dt
    updated_at: dt

    model_config = {"from_attributes": True}


class HighlightSearchResponse(BaseModel):
    """Schema for highlight search response."""

    highlights: list[HighlightSearchResult] = Field(
        default_factory=list, description="List of matching highlights"
    )
    total: int = Field(..., ge=0, description="Total number of results")


class HighlightNoteUpdate(BaseModel):
    """Schema for updating a highlight's note."""

    note: str | None = Field(None, description="Note/annotation text (null to clear)")


class HighlightNoteUpdateResponse(BaseModel):
    """Schema for highlight note update response."""

    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Response message")
    highlight: Highlight = Field(..., description="Updated highlight")
