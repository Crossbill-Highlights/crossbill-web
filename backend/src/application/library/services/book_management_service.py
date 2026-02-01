"""
Book management application service.

Handles CRUD operations and book details aggregation for the library context.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from src import schemas  # Only for input parameter types
from src.application.library.services.book_tag_association_service import (
    BookTagAssociationService,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag
from src.domain.library.services.book_details_aggregator import BookDetailsAggregation
from src.domain.reading.services.highlight_grouping_service import HighlightGroupingService
from src.exceptions import BookNotFoundError
from src.infrastructure.learning.repositories.flashcard_repository import (
    FlashcardRepository,
)
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.reading.repositories.bookmark_repository import BookmarkRepository
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository
from src.repositories.highlight_repository import (
    HighlightRepository as LegacyHighlightRepository,
)
from src.services.ebook.ebook_service import EbookService

logger = logging.getLogger(__name__)

# Directory for book cover images
COVERS_DIR = Path(__file__).parent.parent.parent.parent.parent / "book-files" / "book-covers"


@dataclass
class EreaderMetadata:
    """Lightweight book metadata for ereader operations."""

    book_id: int
    title: str
    author: str | None
    has_cover: bool
    has_ebook: bool


class BookManagementService:
    """Application service for book management operations."""

    def __init__(self, db: Session) -> None:
        """
        Initialize service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.book_repository = BookRepository(db)
        self.bookmark_repository = BookmarkRepository(db)
        self.highlight_repository = HighlightRepository(db)
        self.highlight_grouping_service = HighlightGroupingService()

        # Repositories
        self.flashcard_repository = FlashcardRepository(db)

        # Legacy repositories (temporary)
        self.legacy_highlight_repository = LegacyHighlightRepository(db)

        # Legacy services
        self.ebook_service = EbookService(db)

    def create_book(self, book_data: schemas.BookCreate, user_id: int) -> tuple[Book, bool]:
        """
        Get or create a book based on client_book_id.

        Args:
            book_data: Book creation data
            user_id: ID of the user

        Returns:
            tuple[Book, bool]: (book, created) where created is True if new book was created
        """
        # Convert primitives to value objects
        user_id_vo = UserId(user_id)

        # Primary lookup: client_book_id
        book = self.book_repository.find_by_client_book_id(book_data.client_book_id, user_id_vo)
        if book:
            logger.debug(
                f"Found existing book by client_book_id: {book.title} (id={book.id.value})"
            )
            return book, False

        # Create new book using domain entity factory
        book = Book.create(
            user_id=user_id_vo,
            title=book_data.title,
            client_book_id=book_data.client_book_id,
            author=book_data.author,
            isbn=book_data.isbn,
            description=book_data.description,
            language=book_data.language,
            page_count=book_data.page_count,
            cover=book_data.cover,
        )

        # Save book
        book = self.book_repository.save(book)

        # Add tags using DDD service
        if book_data.keywords:
            tag_service = BookTagAssociationService(self.db)
            tag_service.add_tags_to_book(book.id.value, book_data.keywords, user_id)

        return book, True

    def get_book_details(self, book_id: int, user_id: int) -> BookDetailsAggregation:
        """
        Get detailed information about a book including its chapters and highlights.

        Also updates the book's last_viewed timestamp.

        Args:
            book_id: ID of the book to retrieve
            user_id: ID of the user

        Returns:
            BookDetailsAggregation with aggregated book data

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Fetch and update book (returns domain entity, not ORM)
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        book.mark_as_viewed()
        book = self.book_repository.save(book)

        # Get highlight tags using DDD service (from reading context)
        from src.application.reading.services.highlight_tag_service import (  # noqa: PLC0415
            HighlightTagService,
        )

        highlight_tag_service = HighlightTagService(self.db)
        highlight_tags = highlight_tag_service.get_tags_for_book(book_id, user_id)

        # Get all highlights for book (returns domain entities)
        highlights_with_context = self.highlight_repository.search(
            search_text="",
            user_id=user_id_vo,
            book_id=book_id_vo,
            limit=10000,
        )

        # Use domain service to group highlights
        grouped = self.highlight_grouping_service.group_by_chapter(
            [(h, c, tags, flashcards) for h, _, c, tags, flashcards in highlights_with_context]
        )

        # Get bookmarks (returns domain entities)
        bookmarks = self.bookmark_repository.find_by_book(book_id_vo, user_id_vo)

        # Get tags using DDD service
        tag_service = BookTagAssociationService(self.db)
        tags = tag_service.get_tags_for_book(book_id, user_id)

        # Get legacy book for tag groups (temporary ORM access)
        from src.repositories.book_repository import (  # noqa: PLC0415
            BookRepository as LegacyBookRepository,
        )

        legacy_book_repo = LegacyBookRepository(self.db)
        legacy_book = legacy_book_repo.get_by_id(book_id, user_id)

        # Return domain aggregation
        return BookDetailsAggregation(
            book=book,
            tags=tags,
            highlight_tags=highlight_tags,
            highlight_tag_groups=legacy_book.highlight_tag_groups if legacy_book else [],
            bookmarks=bookmarks,
            chapters_with_highlights=grouped,
        )

    def update_book(
        self, book_id: int, update_data: schemas.BookUpdateRequest, user_id: int
    ) -> tuple[Book, int, int, list[Tag]]:
        """
        Update book information.

        Currently supports updating tags only.

        Args:
            book_id: ID of the book to update
            update_data: Book update request containing tags
            user_id: ID of the user

        Returns:
            Tuple of (book, highlight_count, flashcard_count, tags)

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Verify book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Update tags using DDD service
        tag_service = BookTagAssociationService(self.db)
        tags = tag_service.replace_book_tags(book_id, update_data.tags, user_id)

        # Get counts
        highlight_count = self.legacy_highlight_repository.count_by_book_id(book_id, user_id)
        flashcard_count = self.flashcard_repository.count_by_book(BookId(book_id), UserId(user_id))

        logger.info(f"Successfully updated book {book_id}")

        # Return domain entities
        return (book, highlight_count, flashcard_count, tags)

    def delete_book(self, book_id: int, user_id: int) -> None:
        """
        Delete a book and all its contents (hard delete).

        This will permanently delete the book, all its chapters, highlights,
        cover image, and epub file.

        Args:
            book_id: ID of the book to delete
            user_id: ID of the user

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Verify book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Delete associated epub file if it exists
        self.ebook_service.delete_ebook(book_id)

        # Delete book (cascades handled by database)
        self.book_repository.delete(book)

        logger.info(f"Successfully deleted book {book_id}")

    def get_metadata_for_ereader(self, client_book_id: str, user_id: int) -> EreaderMetadata:
        """
        Get basic book metadata for ereader operations.

        This method returns lightweight book information that KOReader uses to
        decide whether it needs to upload cover images, epub files, etc.

        Args:
            client_book_id: The client-provided book identifier
            user_id: ID of the user

        Returns:
            EreaderMetadata with book info and file availability flags

        Raises:
            BookNotFoundError: If book is not found for the given client_book_id
        """
        # Convert primitives to value objects
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_client_book_id(client_book_id, user_id_vo)
        if not book:
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found"
            )

        # Check if cover file exists
        cover_filename = f"{book.id.value}.jpg"
        cover_path = COVERS_DIR / cover_filename
        has_cover = cover_path.is_file()

        # Check if ebook file exists
        has_ebook = book.file_path is not None

        return EreaderMetadata(
            book_id=book.id.value,
            title=book.title,
            author=book.author,
            has_cover=has_cover,
            has_ebook=has_ebook,
        )
