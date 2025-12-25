"""Pydantic schemas for Flashcard API responses.

This module contains response schemas that combine flashcards with highlights.
It imports from both flashcard_schemas and highlight_schemas to avoid circular
dependencies in those modules.
"""

from pydantic import BaseModel, Field

from src.schemas.flashcard_schemas import Flashcard
from src.schemas.highlight_schemas import HighlightResponseBase


class FlashcardWithHighlight(Flashcard):
    """Flashcard response schema with embedded highlight data."""

    highlight: HighlightResponseBase | None = Field(
        None, description="Associated highlight data with tags (if any)"
    )


class FlashcardsWithHighlightsResponse(BaseModel):
    """Schema for list of flashcards response with highlight data."""

    flashcards: list[FlashcardWithHighlight] = Field(
        default_factory=list, description="List of flashcards with highlight data"
    )
