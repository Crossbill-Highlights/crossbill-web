"""Service layer for highlight-related business logic."""

import structlog
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src import repositories, schemas

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
        background_tasks: BackgroundTasks | None = None,
    ) -> schemas.HighlightUploadResponse:
        """
        Process highlight upload from KOReader.

        This method:
        1. Creates or updates the book record
        2. Creates or retrieves chapter records for highlights with chapter info
        3. Bulk creates highlights with deduplication

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

        # Step 1: Get or create book
        book = self.book_repo.get_or_create(request.book, user_id)

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
                    book.id, user_id, highlight_data.chapter, chapter_number
                )
                chapter_id = chapter.id

            highlights_with_chapters.append((chapter_id, highlight_data))

        # Step 3: Bulk create highlights
        created, skipped = self.highlight_repo.bulk_create(
            book.id, user_id, highlights_with_chapters
        )

        # Commit all changes (book, chapters, highlights)
        self.db.commit()

        message = f"Successfully synced highlights for '{book.title}'"
        logger.info(
            "upload_complete",
            book_id=book.id,
            book_title=book.title,
            highlights_created=created,
            highlights_skipped=skipped,
        )

        return schemas.HighlightUploadResponse(
            success=True,
            message=message,
            book_id=book.id,
            highlights_created=created,
            highlights_skipped=skipped,
        )

    def search_highlights(
        self, search_text: str, user_id: int, book_id: int | None = None, limit: int = 100
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
                chapter_number=highlight.chapter.chapter_number if highlight.chapter else None,
                highlight_tags=highlight.highlight_tags,  # Tags are automatically loaded via lazy="selectin"
                created_at=highlight.created_at,
                updated_at=highlight.updated_at,
            )
            for highlight in highlights
        ]

        return schemas.HighlightSearchResponse(highlights=search_results, total=len(search_results))

    def get_books_with_counts(
        self, user_id: int, offset: int = 0, limit: int = 100, search_text: str | None = None
    ) -> schemas.BooksListResponse:
        """
        Get all books with their highlight counts, sorted alphabetically by title.

        Args:
            user_id: ID of the user
            offset: Number of books to skip (for pagination)
            limit: Maximum number of books to return (for pagination)
            search_text: Optional text to search for in book title or author

        Returns:
            BooksListResponse with list of books and pagination info
        """
        books_with_counts, total = self.book_repo.get_books_with_highlight_count(
            user_id, offset, limit, search_text
        )

        # Convert to response schema
        books_list = [
            schemas.BookWithHighlightCount(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                cover=book.cover,
                highlight_count=count,
                tags=book.tags,  # Tags are automatically loaded via lazy="selectin"
                created_at=book.created_at,
                updated_at=book.updated_at,
            )
            for book, count in books_with_counts
        ]

        return schemas.BooksListResponse(books=books_list, total=total, offset=offset, limit=limit)

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
