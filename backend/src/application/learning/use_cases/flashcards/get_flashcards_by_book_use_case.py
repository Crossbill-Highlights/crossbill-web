"""Use case for retrieving flashcards by book."""

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.learning.use_cases.dtos import FlashcardWithHighlight
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import BookNotFoundError


class GetFlashcardsByBookUseCase:
    """Use case for retrieving flashcards by book."""

    def __init__(
        self,
        flashcard_repository: FlashcardRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
    ) -> None:
        """Initialize use case with repository protocols."""
        self.flashcard_repository = flashcard_repository
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository

    def get_flashcards(self, book_id: int, user_id: int) -> list[FlashcardWithHighlight]:
        """
        Get all flashcards for a book with their associated highlights.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of FlashcardWithHighlight DTOs

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

        # TODO: should we just return tuple of domain objects and then join them to Pydantic schema in router?
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

        return result
