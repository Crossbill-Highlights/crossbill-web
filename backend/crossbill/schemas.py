"""Pydantic schemas for API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class BookBase(BaseModel):
    """Base schema for Book."""

    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str | None = Field(None, max_length=500, description="Book author")
    isbn: str | None = Field(None, max_length=20, description="Book ISBN")


class BookCreate(BookBase):
    """Schema for creating a Book."""


class Book(BookBase):
    """Schema for Book response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterBase(BaseModel):
    """Base schema for Chapter."""

    name: str = Field(..., min_length=1, max_length=500, description="Chapter name")


class Chapter(ChapterBase):
    """Schema for Chapter response."""

    id: int
    book_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HighlightBase(BaseModel):
    """Base schema for Highlight."""

    text: str = Field(..., min_length=1, description="Highlighted text")
    chapter: str | None = Field(None, max_length=500, description="Chapter name")
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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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


class BookWithHighlightCount(BaseModel):
    """Schema for Book with highlight count."""

    id: int
    title: str
    author: str | None
    isbn: str | None
    highlight_count: int = Field(..., ge=0, description="Number of highlights for this book")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BooksListResponse(BaseModel):
    """Schema for paginated books list response."""

    books: list[BookWithHighlightCount] = Field(
        ..., description="List of books with highlight counts"
    )
    total: int = Field(..., ge=0, description="Total number of books")
    offset: int = Field(..., ge=0, description="Current offset")
    limit: int = Field(..., ge=1, description="Current limit")


class ChapterWithHighlights(BaseModel):
    """Schema for Chapter with its highlights."""

    id: int
    name: str
    highlights: list[Highlight] = Field(default_factory=list, description="List of highlights in this chapter")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookDetails(BaseModel):
    """Schema for detailed Book response with chapters and highlights."""

    id: int
    title: str
    author: str | None
    isbn: str | None
    chapters: list[ChapterWithHighlights] = Field(default_factory=list, description="List of chapters with highlights")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
