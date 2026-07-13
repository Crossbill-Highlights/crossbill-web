"""DTOs for note use cases."""

from dataclasses import dataclass

from src.domain.library.entities.chapter import Chapter
from src.domain.notes.entities.note import Note
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag


@dataclass
class NoteWithLinkedEntities:
    """A note together with the linked entities needed for display."""

    note: Note
    chapters: list[Chapter]
    highlights: list[Highlight]
    highlight_tags: list[HighlightTag]
