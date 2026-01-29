"""
Flashcard entity for spaced repetition learning.
"""

from dataclasses import dataclass
from datetime import datetime

from src.domain.common.entity import Entity
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects import BookId, FlashcardId, HighlightId, UserId


@dataclass
class Flashcard(Entity[FlashcardId]):
    """
    Flashcard for creating study cards from highlights.

    Business Rules:
    - Question and answer cannot be empty
    - Flashcard can optionally be linked to a highlight
    - Flashcard must be associated with a book
    """

    id: FlashcardId
    user_id: UserId
    book_id: BookId
    question: str
    answer: str
    created_at: datetime
    updated_at: datetime
    highlight_id: HighlightId | None = None

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.question or not self.question.strip():
            raise DomainError("Question cannot be empty")
        if not self.answer or not self.answer.strip():
            raise DomainError("Answer cannot be empty")

    def update_question(self, question: str) -> None:
        """
        Update the question.

        Args:
            question: New question text

        Raises:
            DomainError: If question is empty
        """
        if not question or not question.strip():
            raise DomainError("Question cannot be empty")
        self.question = question.strip()

    def update_answer(self, answer: str) -> None:
        """
        Update the answer.

        Args:
            answer: New answer text

        Raises:
            DomainError: If answer is empty
        """
        if not answer or not answer.strip():
            raise DomainError("Answer cannot be empty")
        self.answer = answer.strip()
