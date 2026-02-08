from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AIFlashcardSuggestion:
    question: str
    answer: str


class AIFlashcardServiceProtocol(Protocol):
    async def generate_flashcard_suggestions(self, content: str) -> list[AIFlashcardSuggestion]: ...
