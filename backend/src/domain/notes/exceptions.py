"""Notes domain exceptions."""

from src.domain.common.exceptions import EntityNotFoundError, ValidationError


class NoteNotFoundError(EntityNotFoundError):
    """Raised when a note cannot be found."""

    def __init__(self, note_id: int) -> None:
        super().__init__("Note", note_id)
        self.note_id = note_id


class NoteLinkBookMismatchError(ValidationError):
    """Raised when a linked chapter/highlight/tag does not belong to a linked book."""

    def __init__(self, entity_type: str, entity_id: int) -> None:
        super().__init__(f"{entity_type} {entity_id} does not belong to a book linked to this note")
