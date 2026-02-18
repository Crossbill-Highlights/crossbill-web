"""Pydantic schemas for Highlight API request/response validation."""

from datetime import datetime as dt
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, model_validator

from src.infrastructure.library.schemas.book_schemas import TagInBook
from src.infrastructure.reading.schemas.bookmark_schemas import Bookmark
from src.infrastructure.reading.schemas.highlight_tag_schemas import (
    HighlightTagGroupInBook,
    HighlightTagInBook,
)

if TYPE_CHECKING:
    # Import at runtime is handled below to avoid circular imports
    pass

# Import Flashcard after defining HighlightResponseBase to avoid circular imports
# This will be moved after the class definitions


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

    start_xpoint: str | None = Field(None, description="Highlight start position in XML document")
    end_xpoint: str | None = Field(None, description="Highlight end position in XML document")
    color: str | None = Field(
        None, description="Highlight color from KOReader (e.g. 'gray', 'yellow')"
    )
    drawer: str | None = Field(
        None, description="Highlight drawer/style from KOReader (e.g. 'lighten', 'strikethrough')"
    )


class HighlightResponseBase(HighlightBase):
    """Base schema for Highlight response (without flashcards).

    Use this when you need highlight data but don't want nested flashcards.
    """

    id: int
    book_id: int
    chapter_id: int | None
    highlight_style_id: int | None = Field(None, description="ID of the highlight style")
    label: str | None = Field(None, description="Resolved label for this highlight")
    ui_color: str | None = Field(None, description="Resolved UI color for this highlight")
    highlight_tags: list[HighlightTagInBook] = Field(
        ..., description="List of highlight tags for this highlight"
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


# Import Flashcard after HighlightResponseBase is defined to avoid circular import issues
from src.infrastructure.learning.schemas.flashcard_schemas import Flashcard  # noqa: E402


class Highlight(HighlightResponseBase):
    """Schema for Highlight response with flashcards."""

    flashcards: list[Flashcard] = Field(..., description="List of flashcards for this highlight")


class HighlightUploadRequest(BaseModel):
    """Schema for uploading highlights from KOReader."""

    client_book_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Client-provided stable book identifier for deduplication",
    )
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


class PositionResponse(BaseModel):
    """Position in a book document."""

    index: int = Field(..., description="Document-order element number")
    char_index: int = Field(..., description="Character offset within element")


class ChapterWithHighlights(BaseModel):
    """Schema for Chapter with its highlights."""

    id: int
    name: str
    chapter_number: int | None = Field(None, description="Chapter order number from TOC")
    parent_id: int | None = Field(None, description="Parent chapter ID for hierarchy")
    start_position: PositionResponse | None = Field(None, description="Chapter start position")
    highlights: list[Highlight] = Field(..., description="List of highlights in this chapter")
    created_at: dt
    updated_at: dt

    model_config = {"from_attributes": True}


class BookDetails(BaseModel):
    """Schema for detailed Book response with chapters and highlights."""

    id: int
    client_book_id: str | None = None
    title: str
    author: str | None
    isbn: str | None
    cover: str | None
    description: str | None = None
    language: str | None = None
    page_count: int | None = None
    tags: list[TagInBook] = Field(..., description="List of tags for this book")
    highlight_tags: list[HighlightTagInBook] = Field(
        ..., description="List of highlight tags for this book"
    )
    highlight_tag_groups: list[HighlightTagGroupInBook] = Field(
        ..., description="List of highlight tag groups for this book"
    )
    bookmarks: list[Bookmark] = Field(..., description="List of bookmarks for this book")
    book_flashcards: list[Flashcard] = Field(
        default_factory=list,
        description="Book-level flashcards not associated with any highlight",
    )
    chapters: list[ChapterWithHighlights] = Field(
        ..., description="List of chapters with highlights"
    )
    reading_position: PositionResponse | None = Field(
        None, description="User's current reading position from latest session"
    )
    created_at: dt
    updated_at: dt
    last_viewed: dt | None = None

    model_config = {"from_attributes": True}


class HighlightLabelInBook(BaseModel):
    """Schema for a highlight label as shown in book context."""

    id: int
    device_color: str | None = Field(None, description="Device highlight color")
    device_style: str | None = Field(None, description="Device drawing style")
    label: str | None = Field(None, description="User-assigned label")
    ui_color: str | None = Field(None, description="User-chosen UI color")
    label_source: str = Field(..., description="Where the label comes from: 'book', 'global', or 'none'")
    highlight_count: int = Field(..., description="Number of highlights using this style")


class HighlightLabelUpdate(BaseModel):
    """Schema for updating a highlight label."""

    label: str | None = Field(None, description="New label (null to clear)")
    ui_color: str | None = Field(None, description="New UI color (null to clear)")


class HighlightLabelCreate(BaseModel):
    """Schema for creating a global highlight label."""

    device_color: str | None = Field(None, description="Device color to label")
    device_style: str | None = Field(None, description="Device style to label")
    label: str | None = Field(None, description="Label to assign")
    ui_color: str | None = Field(None, description="UI color to assign")


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


class BookHighlightSearchResponse(BaseModel):
    """Schema for book-scoped highlight search response grouped by chapter."""

    chapters: list[ChapterWithHighlights] = Field(
        ..., description="Chapters containing matching highlights"
    )
    total: int = Field(..., ge=0, description="Total number of matching highlights")


class HighlightNoteUpdate(BaseModel):
    """Schema for updating a highlight's note."""

    note: str | None = Field(None, description="Note/annotation text (null to clear)")


class HighlightNoteUpdateResponse(BaseModel):
    """Schema for highlight note update response."""

    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Response message")
    highlight: Highlight = Field(..., description="Updated highlight")
