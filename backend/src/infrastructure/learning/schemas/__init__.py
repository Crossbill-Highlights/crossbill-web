"""Learning context schemas."""

from src.infrastructure.learning.schemas.flashcard_api_schemas import (
    FlashcardsWithHighlightsResponse,
    FlashcardWithHighlight,
)
from src.infrastructure.learning.schemas.flashcard_schemas import (
    Flashcard,
    FlashcardCreateRequest,
    FlashcardCreateResponse,
    FlashcardDeleteResponse,
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
    "FlashcardDeleteResponse",
    "FlashcardSuggestionItem",
    "FlashcardUpdateRequest",
    "FlashcardUpdateResponse",
    "FlashcardWithHighlight",
    "FlashcardsWithHighlightsResponse",
    "HighlightFlashcardSuggestionsResponse",
    "NoteFlashcardCreateRequest",
]
