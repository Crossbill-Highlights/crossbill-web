"""Service layer for highlight-related business logic."""

import structlog
from sqlalchemy.orm import Session

from src import repositories, schemas
from src.services.book_service import BookService
from src.utils import compute_highlight_hash

logger = structlog.get_logger(__name__)


class HighlightService:
    """Service for handling highlight-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.chapter_repo = repositories.ChapterRepository(db)
        self.highlight_repo = repositories.HighlightRepository(db)

    def upload_highlights(
        self,
        request: schemas.HighlightUploadRequest,
        user_id: int,
    ) -> schemas.HighlightUploadResponse:
        """
        Process highlight upload from KOReader.

        This method:
        1. Creates or updates the book record
        2. Batch processes chapters (fetches existing and bulk creates new ones)
        3. Prepares highlights with content hashes
        4. Bulk creates highlights with deduplication

        Args:
            request: Upload request containing book metadata and highlights
            user_id: ID of the user

        Returns:
            HighlightUploadResponse with upload statistics
        """
        logger.info(
            "processing_highlight_upload",
            book_title=request.book.title,
            book_author=request.book.author,
            highlight_count=len(request.highlights),
        )

        # Step 1: Get or create book (with keywords as tags on creation)
        book_service = BookService(self.db)
        book, _ = book_service.create_book(request.book, user_id)

        # Step 2: Batch process chapters using chapter_number
        chapter_numbers: set[int] = set()

        for highlight_data in request.highlights:
            if highlight_data.chapter_number is not None:
                chapter_numbers.add(highlight_data.chapter_number)

        # Fetch existing chapters by chapter_number only
        # Note: EPUB ToC parsing creates chapters, highlights just reference them
        existing_chapters_by_number = self.chapter_repo.get_by_numbers(
            book.id, chapter_numbers, user_id
        )

        # No chapter creation here - chapters come from EPUB ToC upload
        # If a highlight references a non-existent chapter_number, it won't be associated total
        # chapter

        # Commit any pending changes before processing highlights
        self.db.commit()

        # Step 3: Prepare highlights with chapter_number lookup
        highlights_with_chapters: list[tuple[int | None, str, schemas.HighlightCreate]] = []

        for highlight_data in request.highlights:
            chapter_id = None

            # Use chapter_number for lookup (source of truth)
            if highlight_data.chapter_number is not None:
                chapter = existing_chapters_by_number.get(highlight_data.chapter_number)
                if chapter:
                    chapter_id = chapter.id
                else:
                    # Chapter doesn't exist - probably EPUB not uploaded yet
                    logger.warning(
                        "chapter_not_found_for_highlight",
                        chapter_name=highlight_data.chapter,
                        chapter_number=highlight_data.chapter_number,
                        book_id=book.id,
                        message="Chapter referenced by highlight doesn't exist. Upload EPUB to create chapters.",
                    )
            elif highlight_data.chapter:
                # No chapter_number - can't reliably associate with duplicate names
                logger.warning(
                    "highlight_missing_chapter_number",
                    chapter_name=highlight_data.chapter,
                    book_id=book.id,
                    message="Highlight has no chapter_number. Cannot associate reliably with duplicate chapter names.",
                )

            # Compute content hash for deduplication
            content_hash = compute_highlight_hash(
                text=highlight_data.text,
                book_title=request.book.title,
                book_author=request.book.author,
            )

            highlights_with_chapters.append((chapter_id, content_hash, highlight_data))

        # Step 4: Bulk create highlights
        highlights_created, highlights_skipped = self.highlight_repo.bulk_create(
            book.id, user_id, highlights_with_chapters
        )

        # Commit highlights
        self.db.commit()

        message = f"Successfully synced highlights for '{book.title}'"
        logger.info(
            "upload_complete",
            book_id=book.id,
            book_title=book.title,
            highlights_created=highlights_created,
            highlights_skipped=highlights_skipped,
        )

        return schemas.HighlightUploadResponse(
            success=True,
            message=message,
            book_id=book.id,
            highlights_created=highlights_created,
            highlights_skipped=highlights_skipped,
        )

    def search_highlights(
        self,
        search_text: str,
        user_id: int,
        book_id: int | None = None,
        limit: int = 100,
    ) -> schemas.HighlightSearchResponse:
        """
        Search for highlights using full-text search.

        Searches across all highlight text using PostgreSQL full-text search
        or LIKE-based search for SQLite. Results are ranked by relevance and
        exclude soft-deleted highlights.

        Args:
            search_text: Text to search for
            user_id: ID of the user
            book_id: Optional book ID to filter by specific book
            limit: Maximum number of results to return

        Returns:
            HighlightSearchResponse with matching highlights and their book/chapter data
        """
        # Search using repository
        highlights = self.highlight_repo.search(search_text, user_id, book_id, limit)

        # Convert to response schema with book and chapter data
        search_results = [
            schemas.HighlightSearchResult(
                id=highlight.id,
                text=highlight.text,
                page=highlight.page,
                note=highlight.note,
                datetime=highlight.datetime,
                book_id=highlight.book_id,
                book_title=highlight.book.title,
                book_author=highlight.book.author,
                chapter_id=highlight.chapter_id,
                chapter_name=highlight.chapter.name if highlight.chapter else None,
                chapter_number=(highlight.chapter.chapter_number if highlight.chapter else None),
                highlight_tags=[
                    schemas.HighlightTagInBook.model_validate(tag)
                    for tag in highlight.highlight_tags
                ],
                created_at=highlight.created_at,
                updated_at=highlight.updated_at,
            )
            for highlight in highlights
        ]

        return schemas.HighlightSearchResponse(highlights=search_results, total=len(search_results))

    def get_books_with_counts(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        include_only_with_flashcards: bool = False,
        search_text: str | None = None,
    ) -> schemas.BooksListResponse:
        """
        Get all books with their highlight and flashcard counts, sorted alphabetically by title.

        Args:
            user_id: ID of the user
            offset: Number of books to skip (for pagination)
            limit: Maximum number of books to return (for pagination)
            search_text: Optional text to search for in book title or author

        Returns:
            BooksListResponse with list of books and pagination info
        """
        books_with_counts, total = self.book_repo.get_books_with_highlight_count(
            user_id, offset, limit, include_only_with_flashcards, search_text
        )

        # Convert to response schema
        books_list = [
            schemas.BookWithHighlightCount(
                id=book.id,
                client_book_id=book.client_book_id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                cover=book.cover,
                description=book.description,
                language=book.language,
                page_count=book.page_count,
                highlight_count=highlight_count,
                flashcard_count=flashcard_count,
                tags=[schemas.TagInBook.model_validate(tag) for tag in book.tags],
                created_at=book.created_at,
                updated_at=book.updated_at,
                last_viewed=book.last_viewed,
            )
            for book, highlight_count, flashcard_count in books_with_counts
        ]

        return schemas.BooksListResponse(books=books_list, total=total, offset=offset, limit=limit)

    def get_recently_viewed_books(
        self, user_id: int, limit: int = 10
    ) -> schemas.RecentlyViewedBooksResponse:
        """
        Get recently viewed books with their highlight and flashcard counts.

        Only returns books that have been viewed at least once.

        Args:
            user_id: ID of the user
            limit: Maximum number of books to return (default: 10)

        Returns:
            RecentlyViewedBooksResponse with list of recently viewed books
        """
        books_with_counts = self.book_repo.get_recently_viewed_books(user_id, limit)

        # Convert to response schema
        books_list = [
            schemas.BookWithHighlightCount(
                id=book.id,
                client_book_id=book.client_book_id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                cover=book.cover,
                description=book.description,
                language=book.language,
                page_count=book.page_count,
                highlight_count=highlight_count,
                flashcard_count=flashcard_count,
                tags=[schemas.TagInBook.model_validate(tag) for tag in book.tags],
                created_at=book.created_at,
                updated_at=book.updated_at,
                last_viewed=book.last_viewed,
            )
            for book, highlight_count, flashcard_count in books_with_counts
        ]

        return schemas.RecentlyViewedBooksResponse(books=books_list)

    def update_highlight_note(
        self, highlight_id: int, user_id: int, note_data: schemas.HighlightNoteUpdate
    ) -> schemas.Highlight | None:
        """
        Update the note field of a highlight.

        Args:
            highlight_id: ID of the highlight to update
            user_id: ID of the user
            note_data: Note update data

        Returns:
            Updated highlight or None if not found
        """
        # Update the note using repository
        highlight = self.highlight_repo.update_note(highlight_id, user_id, note_data.note)

        if highlight is None:
            return None

        # Commit the changes
        self.db.commit()
        self.db.refresh(highlight)

        logger.info("highlight_note_updated", highlight_id=highlight_id)

        # Convert to response schema
        return schemas.Highlight.model_validate(highlight)


# Keep the old name for backwards compatibility
HighlightUploadService = HighlightService
