"""DTOs for flashcard AI use cases."""

from dataclasses import dataclass


@dataclass
class FlashcardSuggestion:
    """Simple data class for AI suggestions."""

    question: str
    answer: str
