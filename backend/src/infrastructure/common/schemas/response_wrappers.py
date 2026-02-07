"""Common response wrapper schemas for API responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Generic success response wrapper."""

    success: bool
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic pagination wrapper."""

    items: list[T]
    total: int
    offset: int
    limit: int
