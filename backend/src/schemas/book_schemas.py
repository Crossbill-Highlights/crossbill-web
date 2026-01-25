"""Pydantic schemas for Book API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class BookBase(BaseModel):
    """Base schema for Book."""

    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str | None = Field(None, max_length=500, description="Book author")
    isbn: str | None = Field(None, max_length=20, description="Book ISBN")
    cover: str | None = Field(None, max_length=500, description="Book cover image path")
    description: str | None = Field(None, description="Book description from ebook metadata")
    language: str | None = Field(
        None, max_length=10, description="Language code from ebook metadata"
    )
    page_count: int | None = Field(None, ge=1, description="Total page count from ebook metadata")


class BookCreate(BookBase):
    """Schema for creating a Book."""

    client_book_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Client-provided stable book identifier for deduplication",
    )
    keywords: list[str] | None = Field(
        None, description="Keywords from ebook metadata (will be converted to tags)"
    )


class Book(BookBase):
    """Schema for Book response."""

    id: int
    client_book_id: str | None = None
    created_at: datetime
    updated_at: datetime
    last_viewed: datetime | None = None

    model_config = {"from_attributes": True}


class TagInBook(BaseModel):
    """Minimal tag schema for book responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class BookWithHighlightCount(BaseModel):
    """Schema for Book with highlight and flashcard counts."""

    id: int
    client_book_id: str | None = None
    title: str
    author: str | None
    isbn: str | None
    cover: str | None
    description: str | None = None
    language: str | None = None
    page_count: int | None = None
    highlight_count: int = Field(..., ge=0, description="Number of highlights for this book")
    flashcard_count: int = Field(0, ge=0, description="Number of flashcards for this book")
    tags: list[TagInBook] = Field(..., description="List of tags for this book")
    created_at: datetime
    updated_at: datetime
    last_viewed: datetime | None = None

    model_config = {"from_attributes": True}


class BooksListResponse(BaseModel):
    """Schema for paginated books list response."""

    books: list[BookWithHighlightCount] = Field(
        ..., description="List of books with highlight counts"
    )
    total: int = Field(..., ge=0, description="Total number of books")
    offset: int = Field(..., ge=0, description="Current offset")
    limit: int = Field(..., ge=1, description="Current limit")


class RecentlyViewedBooksResponse(BaseModel):
    """Schema for recently viewed books response."""

    books: list[BookWithHighlightCount] = Field(
        ..., description="List of recently viewed books with highlight counts"
    )


class CoverUploadResponse(BaseModel):
    """Schema for cover upload response."""

    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")
    cover_url: str = Field(..., description="URL path to the uploaded cover image")


class EpubUploadResponse(BaseModel):
    """Schema for epub upload response."""

    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")


class EreaderBookMetadata(BaseModel):
    """Schema for ereader book metadata response.

    This lightweight response is used by KOReader to get basic book information
    for deciding whether to upload cover images, epub files, etc.
    """

    book_id: int = Field(..., description="Internal book ID")
    bookname: str = Field(..., description="Book title")
    author: str | None = Field(None, description="Book author")
    has_cover: bool = Field(..., description="Whether the book has a cover image")
    has_ebook: bool = Field(..., description="Whether the book has an ebook file")
