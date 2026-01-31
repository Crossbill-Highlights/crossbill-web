"""
Update highlight note use case.

Updates the note field of a highlight using domain entity behavior.
"""

from sqlalchemy.orm import Session

from src.domain.common.value_objects import HighlightId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository


class UpdateHighlightNoteService:
    """Application service for updating highlight notes."""

    def __init__(self, db: Session) -> None:
        """
        Initialize service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.highlight_repository = HighlightRepository(db)

    def update_note(
        self, highlight_id: int, user_id: int, note: str | None
    ) -> tuple[Highlight, list[Flashcard], list[HighlightTag]] | None:
        """
        Update a highlight's note field.

        Uses the domain entity's update_note() method to enforce business rules.

        Args:
            highlight_id: ID of the highlight to update
            user_id: ID of the user who owns the highlight
            note: New note text (or None to clear)

        Returns:
            Tuple of (Updated Highlight, Flashcards, HighlightTags) or None if not found
        """
        # Convert primitives to value objects
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        # Load highlight
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)

        if highlight is None:
            return None

        # Use domain entity's command method
        highlight.update_note(note)

        # Persist changes
        self.highlight_repository.save(highlight)

        # Flush to ensure relationships are available
        self.db.flush()

        # Load with relations to return complete data
        result = self.highlight_repository.find_by_id_with_relations(highlight_id_vo, user_id_vo)

        if result is None:
            return None

        return result
