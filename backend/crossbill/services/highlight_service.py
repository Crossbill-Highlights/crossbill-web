"""Service layer for highlight-related business logic."""

import logging

from sqlalchemy.orm import Session

from crossbill import repositories, schemas

logger = logging.getLogger(__name__)


class HighlightUploadService:
    """Service for handling highlight uploads from KOReader."""

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
