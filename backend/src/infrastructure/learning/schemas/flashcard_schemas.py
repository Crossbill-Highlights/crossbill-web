"""Pydantic schemas for Flashcard API request/response validation."""

from pydantic import BaseModel, Field


class FlashcardBase(BaseModel):
    """Base schema for Flashcard."""

    question: str = Field(..., min_length=1, description="Question text for the flashcard")
    answer: str = Field(..., min_length=1, description="Answer text for the flashcard")


class FlashcardCreate(FlashcardBase):
    """Schema for creating a flashcard."""

    highlight_id: int | None = Field(None, description="Optional highlight ID to associate with")


class Flashcard(FlashcardBase):
    """Schema for Flashcard response (without embedded highlight)."""

    id: int
    user_id: int
    book_id: int
    highlight_id: int | None
    chapter_id: int | None = None

    model_config = {"from_attributes": True}


class FlashcardCreateRequest(BaseModel):
    """Schema for creating a new flashcard."""

    question: str = Field(..., min_length=1, description="Question text for the flashcard")
    answer: str = Field(..., min_length=1, description="Answer text for the flashcard")
    chapter_id: int | None = Field(None, description="Optional chapter ID to associate with")


class FlashcardCreateResponse(BaseModel):
    """Schema for flashcard creation response."""

    success: bool = Field(..., description="Whether the creation was successful")
    message: str = Field(..., description="Response message")
    flashcard: Flashcard = Field(..., description="Created flashcard")


class FlashcardUpdateRequest(BaseModel):
    """Schema for updating a flashcard."""

    question: str | None = Field(None, min_length=1, description="New question text")
    answer: str | None = Field(None, min_length=1, description="New answer text")


class FlashcardUpdateResponse(BaseModel):
    """Schema for flashcard update response."""

    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Response message")
    flashcard: Flashcard = Field(..., description="Updated flashcard")


class FlashcardDeleteResponse(BaseModel):
    """Schema for flashcard deletion response."""

    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")


class FlashcardsListResponse(BaseModel):
    """Schema for list of flashcards response."""

    flashcards: list[Flashcard] = Field(..., description="List of flashcards")


class FlashcardSuggestionItem(BaseModel):
    """Schema for a single AI-generated flashcard suggestion."""

    question: str = Field(..., description="Suggested question for flashcard")
    answer: str = Field(..., description="Suggested answer for flashcard")


class HighlightFlashcardSuggestionsResponse(BaseModel):
    """Schema for flashcard suggestions response."""

    suggestions: list[FlashcardSuggestionItem] = Field(
        ..., description="List of AI-generated flashcard suggestions"
    )
