"""
Domain-centric service for highlight use cases.

Orchestrates highlight upload using domain entities and repositories.
No Pydantic dependencies - works with domain entities only.
"""

from dataclasses import dataclass

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects import BookId, ChapterId, UserId, XPointRange
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.exceptions import BookNotFoundError
from src.domain.reading.services.deduplication_service import HighlightDeduplicationService
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository
from src.repositories import BookRepository, ChapterRepository

logger = structlog.get_logger(__name__)


@dataclass
class HighlightUploadData:
    """
    Simple data class for passing highlight data from API layer to service layer.
    """

    text: str
    chapter_number: int | None = None
    chapter: str | None = None  # Chapter name (for warning logs)
    start_xpoint: str | None = None
    end_xpoint: str | None = None
    page: int | None = None
    note: str | None = None


class HighlightService:
    """Domain-centric service for highlight operations."""

    def __init__(self, db: Session) -> None:
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.highlight_repo = HighlightRepository(db)
        # TODO: Legacy repositories (for now - will migrate later)
        self.book_repo = BookRepository(db)
        self.chapter_repo = ChapterRepository(db)
        self.deduplication_service = HighlightDeduplicationService()

    def upload_highlights(
        self,
        client_book_id: str,
        highlight_data_list: list[HighlightUploadData],
        user_id: int,
    ) -> tuple[int, int]:
        """
        Process highlight upload from KOReader.

        This method:
        1. Looks up the existing book by client_book_id
        2. Batch fetches chapters by chapter_number
        3. Creates domain entities using factory methods
        4. Deduplicates using domain service
        5. Bulk saves unique highlights

        Args:
            client_book_id: Book identifier from client
            highlight_data_list: List of highlight data to upload
            user_id: User ID (primitive int, converted to value object)

        Returns:
            Tuple of (created_count, skipped_count)

        Raises:
            BookNotFoundError: If book doesn't exist
        """
        logger.info(
            "processing_highlight_upload",
            book_client_id=client_book_id,
            highlight_count=len(highlight_data_list),
        )

        # Convert primitive to value object
        user_id_vo = UserId(user_id)

        # Step 1: Find book (returns ORM model for now - legacy repository)
        book_orm = self.book_repo.find_by_client_book_id(client_book_id, user_id)

        if not book_orm:
            logger.error(
                "book_not_found_for_highlight_upload",
                client_book_id=client_book_id,
            )
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found. "
                "Please create the book first"
            )

        book_id = BookId(book_orm.id)

        # Step 2: Batch fetch chapters by chapter_number
        chapter_numbers: set[int] = {
            data.chapter_number for data in highlight_data_list if data.chapter_number is not None
        }

        # Returns dict[int, Chapter ORM model]
        chapters_by_number = self.chapter_repo.get_by_numbers(book_orm.id, chapter_numbers, user_id)

        # Step 3: Create domain entities using factory methods
        new_highlights: list[Highlight] = []

        for data in highlight_data_list:
            # Resolve chapter ID
            chapter_id: ChapterId | None = None
            if data.chapter_number is not None:
                chapter_orm = chapters_by_number.get(data.chapter_number)
                if chapter_orm:
                    chapter_id = ChapterId(chapter_orm.id)
                else:
                    logger.warning(
                        "chapter_not_found_for_highlight",
                        chapter_number=data.chapter_number,
                        book_id=book_orm.id,
                        message="Chapter referenced by highlight doesn't exist. Upload EPUB to create chapters.",
                    )
            elif data.chapter:
                # No chapter_number - can't reliably associate with duplicate names
                logger.warning(
                    "highlight_missing_chapter_number",
                    chapter_name=data.chapter,
                    book_id=book_orm.id,
                    message="Highlight has no chapter_number. Cannot associate reliably with duplicate chapter names.",
                )

            xpoints: XPointRange | None = None
            if data.start_xpoint and data.end_xpoint:
                xpoints = XPointRange.parse(data.start_xpoint, data.end_xpoint)

            highlight = Highlight.create(
                user_id=user_id_vo,
                book_id=book_id,
                text=data.text,
                chapter_id=chapter_id,
                xpoints=xpoints,
                page=data.page,
                note=data.note,
            )
            new_highlights.append(highlight)

        # Step 4: Deduplication using domain service
        existing_hashes = self.highlight_repo.get_existing_hashes(
            user_id_vo, book_id, [h.content_hash for h in new_highlights]
        )

        unique, duplicates = self.deduplication_service.find_duplicates(
            new_highlights, existing_hashes
        )

        # Step 5: Bulk save unique highlights
        if unique:
            self.highlight_repo.bulk_save(unique)

        # Step 6: Commit transaction
        self.db.commit()

        logger.info(
            "upload_complete",
            book_id=book_orm.id,
            book_title=book_orm.title,
            highlights_created=len(unique),
            highlights_skipped=len(duplicates),
        )

        return len(unique), len(duplicates)
