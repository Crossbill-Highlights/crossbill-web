"""Pydantic schemas for Book API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class BookBase(BaseModel):
    """Base schema for Book."""

    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str | None = Field(None, max_length=500, description="Book author")
    isbn: str | None = Field(None, max_length=20, description="Book ISBN")
    cover: str | None = Field(None, max_length=500, description="Book cover image path")


class BookCreate(BookBase):
    """Schema for creating a Book."""


class Book(BookBase):
    """Schema for Book response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagInBook(BaseModel):
    """Minimal tag schema for book responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class BookWithHighlightCount(BaseModel):
    """Schema for Book with highlight count."""

    id: int
    title: str
    author: str | None
    isbn: str | None
    cover: str | None
    highlight_count: int = Field(..., ge=0, description="Number of highlights for this book")
    tags: list[TagInBook] = Field(default_factory=list, description="List of tags for this book")
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


class CoverUploadResponse(BaseModel):
    """Schema for cover upload response."""

    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")
    cover_url: str = Field(..., description="URL path to the uploaded cover image")
