"""Service layer for highlight-related business logic."""

import logging

from sqlalchemy.orm import Session

from crossbill import repositories, schemas

logger = logging.getLogger(__name__)


class HighlightService:
    """Service for handling highlight-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.chapter_repo = repositories.ChapterRepository(db)
        self.highlight_repo = repositories.HighlightRepository(db)

    def upload_highlights(
        self, request: schemas.HighlightUploadRequest
    ) -> schemas.HighlightUploadResponse:
        """
        Process highlight upload from KOReader.

        This method:
        1. Creates or updates the book record
        2. Creates or retrieves chapter records for highlights with chapter info
        3. Bulk creates highlights with deduplication

        Args:
            request: Upload request containing book metadata and highlights

        Returns:
            HighlightUploadResponse with upload statistics
        """
        logger.info(f"Processing highlight upload for book: {request.book.title}")

        # Step 1: Get or create book
        book = self.book_repo.get_or_create(request.book)

        # Step 2: Process chapters and prepare highlights
        highlights_with_chapters: list[tuple[int | None, schemas.HighlightCreate]] = []

        for highlight_data in request.highlights:
            chapter_id = None

            # If highlight has chapter info, get or create the chapter
            if highlight_data.chapter:
                # Use chapter_number from the highlight (set by KOReader plugin)
                chapter_number = highlight_data.chapter_number

                # Get or create chapter with the chapter number
                chapter = self.chapter_repo.get_or_create(
                    book.id, highlight_data.chapter, chapter_number
                )
                chapter_id = chapter.id

            highlights_with_chapters.append((chapter_id, highlight_data))

        # Step 3: Bulk create highlights
        created, skipped = self.highlight_repo.bulk_create(book.id, highlights_with_chapters)

        message = f"Successfully synced highlights for '{book.title}'"
        logger.info(
            f"Upload complete for book '{book.title}' (id={book.id}): "
            f"{created} created, {skipped} skipped"
        )

        return schemas.HighlightUploadResponse(
            success=True,
            message=message,
            book_id=book.id,
            highlights_created=created,
            highlights_skipped=skipped,
        )

    def search_highlights(
        self, search_text: str, book_id: int | None = None, limit: int = 100
    ) -> schemas.HighlightSearchResponse:
        """
        Search for highlights using full-text search.

        Searches across all highlight text using PostgreSQL full-text search
        or LIKE-based search for SQLite. Results are ranked by relevance and
        exclude soft-deleted highlights.

        Args:
            search_text: Text to search for
            book_id: Optional book ID to filter by specific book
            limit: Maximum number of results to return

        Returns:
            HighlightSearchResponse with matching highlights and their book/chapter data
        """
        # Search using repository
        highlights = self.highlight_repo.search(search_text, book_id, limit)

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
                chapter_number=highlight.chapter.chapter_number if highlight.chapter else None,
                created_at=highlight.created_at,
                updated_at=highlight.updated_at,
            )
            for highlight in highlights
        ]

        return schemas.HighlightSearchResponse(
            highlights=search_results, total=len(search_results)
        )

    def get_books_with_counts(
        self, offset: int = 0, limit: int = 100
    ) -> schemas.BooksListResponse:
        """
        Get all books with their highlight counts, sorted alphabetically by title.

        Args:
            offset: Number of books to skip (for pagination)
            limit: Maximum number of books to return (for pagination)

        Returns:
            BooksListResponse with list of books and pagination info
        """
        books_with_counts, total = self.book_repo.get_books_with_highlight_count(offset, limit)

        # Convert to response schema
        books_list = [
            schemas.BookWithHighlightCount(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                cover=book.cover,
                highlight_count=count,
                created_at=book.created_at,
                updated_at=book.updated_at,
            )
            for book, count in books_with_counts
        ]

        return schemas.BooksListResponse(books=books_list, total=total, offset=offset, limit=limit)


# Keep the old name for backwards compatibility
HighlightUploadService = HighlightService
