"""Use case for retrieving flashcards by book."""

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.learning.use_cases.dtos import FlashcardWithHighlight
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.domain.reading.services.highlight_style_resolver import (
    HighlightStyleResolver,
    ResolvedLabel,
)
from src.exceptions import BookNotFoundError


class GetFlashcardsByBookUseCase:
    """Use case for retrieving flashcards by book."""

    def __init__(
        self,
        flashcard_repository: FlashcardRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_style_repository: HighlightStyleRepositoryProtocol | None = None,
        highlight_style_resolver: HighlightStyleResolver | None = None,
    ) -> None:
        """Initialize use case with repository protocols."""
        self.flashcard_repository = flashcard_repository
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository
        self.highlight_style_repository = highlight_style_repository
        self.highlight_style_resolver = highlight_style_resolver

    def get_flashcards(
        self, book_id: int, user_id: int
    ) -> tuple[list[FlashcardWithHighlight], dict[int, ResolvedLabel]]:
        """
        Get all flashcards for a book with their associated highlights.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            Tuple of (FlashcardWithHighlight DTOs, resolved labels)

        Raises:
            BookNotFoundError: If book is not found
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        flashcards = self.flashcard_repository.find_by_book(book_id_vo, user_id_vo)

        highlight_ids = [fc.highlight_id for fc in flashcards if fc.highlight_id is not None]

        highlight_map: dict[int, tuple[Highlight, Chapter | None, list[HighlightTag]]] = {}
        if highlight_ids:
            highlights_data = self.highlight_repository.find_by_ids_with_tags(
                highlight_ids, user_id_vo
            )
            highlight_map = {h.id.value: (h, chapter, tags) for h, chapter, tags in highlights_data}

        # Combine flashcards with their highlights
        result = []
        for fc in flashcards:
            highlight = None
            chapter = None
            tags = []
            if fc.highlight_id:
                highlight_data = highlight_map.get(fc.highlight_id.value)
                if highlight_data:
                    highlight, chapter, tags = highlight_data

            result.append(
                FlashcardWithHighlight(
                    flashcard=fc, highlight=highlight, chapter=chapter, highlight_tags=tags
                )
            )

        # Resolve labels
        labels: dict[int, ResolvedLabel] = {}
        if self.highlight_style_repository and self.highlight_style_resolver:
            all_styles = self.highlight_style_repository.find_for_resolution(user_id_vo, book_id_vo)
            for style in all_styles:
                if style.is_combination_level() and not style.is_global():
                    resolved = self.highlight_style_resolver.resolve(style, all_styles)
                    labels[style.id.value] = resolved

        return result, labels
