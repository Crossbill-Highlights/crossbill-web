"""Learning context schemas."""

from src.infrastructure.learning.schemas.flashcard_api_schemas import (
    FlashcardsWithHighlightsResponse,
    FlashcardWithHighlight,
)
from src.infrastructure.learning.schemas.flashcard_schemas import (
    Flashcard,
    FlashcardBase,
    FlashcardCreate,
    FlashcardCreateRequest,
    FlashcardCreateResponse,
    FlashcardDeleteResponse,
    FlashcardsListResponse,
    FlashcardSuggestionItem,
    FlashcardUpdateRequest,
    FlashcardUpdateResponse,
    HighlightFlashcardSuggestionsResponse,
)

__all__ = [
    "Flashcard",
    "FlashcardBase",
    "FlashcardCreate",
    "FlashcardCreateRequest",
    "FlashcardCreateResponse",
    "FlashcardDeleteResponse",
    "FlashcardSuggestionItem",
    "FlashcardUpdateRequest",
    "FlashcardUpdateResponse",
    "FlashcardWithHighlight",
    "FlashcardsListResponse",
    "FlashcardsWithHighlightsResponse",
    "HighlightFlashcardSuggestionsResponse",
]
