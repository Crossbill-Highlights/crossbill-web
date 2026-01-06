"""Pydantic schemas for Reading Session API request/response validation."""

from datetime import datetime as dt
from typing import Self

from pydantic import BaseModel, Field, model_validator

from src.schemas.book_schemas import BookCreate


class ReadingSessionBase(BaseModel):
    """Base schema for ReadingSession."""

    book_id: int
    device_id: str | None
    content_hash: str
    start_time: dt = Field(..., description="Session start timestamp")
    end_time: dt = Field(..., description="Session end timestamp")
    start_xpoint: str | None = Field(None, description="EPUB XML start position")
    end_xpoint: str | None = Field(None, description="EPUB XML end position")
    start_page: int | None = Field(None, ge=0, description="Start page number (for PDFs)")
    end_page: int | None = Field(None, ge=0, description="End page number (for PDFs)")

    @model_validator(mode="after")
    def check_position_fields(self) -> Self:
        has_xpoint = self.start_xpoint is not None and self.end_xpoint is not None
        has_page = self.start_page is not None and self.end_page is not None

        if not has_xpoint and not has_page:
            raise ValueError(
                "You must define at least either (start_xpoint & end_xpoint) or (start_page & end_page)."
            )

        return self


class ReadingSession(ReadingSessionBase):
    """Schema for ReadingSession response."""

    id: int
    created_at: dt

    model_config = {"from_attributes": True}


class ReadingSessionUploadSessionItem(BaseModel):
    """Schema for a single reading session in the upload request."""

    start_time: dt = Field(..., description="Session start timestamp")
    end_time: dt = Field(..., description="Session end timestamp")
    start_xpoint: str | None = Field(None, description="Start position (xpoint string)")
    end_xpoint: str | None = Field(None, description="End position (xpoint string)")
    start_page: int | None = Field(None, ge=0, description="Start page for PDFs")
    end_page: int | None = Field(None, ge=0, description="End page for PDFs")
    device_id: str | None = Field(None, max_length=100, description="Device identifier")

    @model_validator(mode="after")
    def check_position_fields(self) -> Self:
        """Validate that at least one position type is provided."""
        has_xpoint = self.start_xpoint is not None and self.end_xpoint is not None
        has_page = self.start_page is not None and self.end_page is not None

        if not has_xpoint and not has_page:
            raise ValueError(
                "You must define at least either (start_xpoint & end_xpoint) "
                "or (start_page & end_page)."
            )
        return self


class ReadingSessionUploadRequest(BaseModel):
    """Schema for uploading reading sessions from KOReader."""

    book: BookCreate = Field(..., description="Book metadata for all sessions in this request")
    sessions: list[ReadingSessionUploadSessionItem] = Field(
        ..., min_length=1, description="List of reading sessions for this book"
    )


class ReadingSessionUploadResponse(BaseModel):
    """Schema for reading session upload response.

    Note: If any session is invalid,
    the entire request fails with 422 and this response is never returned.
    """

    success: bool = Field(..., description="Whether the upload was successful (always True)")
    message: str = Field(..., description="Response message")
    created_count: int = Field(0, description="Number of sessions created")
    skipped_duplicate_count: int = Field(0, description="Sessions skipped because already uploaded")


class ReadingSessionsResponse(BaseModel):
    """Schema for list of reading sessions response."""

    sessions: list[ReadingSession] = Field(..., description="List of reading sessions")
    total: int = Field(..., ge=0, description="Total number of sessions")
