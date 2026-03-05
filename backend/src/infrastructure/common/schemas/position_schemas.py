"""Shared position schemas used across multiple domain schema modules."""

from pydantic import BaseModel, Field


class PositionResponse(BaseModel):
    """Position in a book document."""

    index: int = Field(..., description="Document-order element number")
    char_index: int = Field(..., description="Character offset within element")
