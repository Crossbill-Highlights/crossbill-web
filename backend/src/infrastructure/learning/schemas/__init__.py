"""Learning context schemas."""

from src.infrastructure.learning.schemas.flashcard_api_schemas import (
    FlashcardsWithHighlightsResponse,
    FlashcardWithHighlight,
)
from src.infrastructure.learning.schemas.flashcard_schemas import (
    Flashcard,
    FlashcardCreateRequest,
    FlashcardCreateResponse,
    FlashcardSuggestionItem,
    FlashcardUpdateRequest,
    FlashcardUpdateResponse,
    HighlightFlashcardSuggestionsResponse,
    NoteFlashcardCreateRequest,
)

__all__ = [
    "Flashcard",
    "FlashcardCreateRequest",
    "FlashcardCreateResponse",
    "FlashcardSuggestionItem",
    "FlashcardUpdateRequest",
    "FlashcardUpdateResponse",
    "FlashcardWithHighlight",
    "FlashcardsWithHighlightsResponse",
    "HighlightFlashcardSuggestionsResponse",
    "NoteFlashcardCreateRequest",
]
