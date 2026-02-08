import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.library.entities.chapter import Chapter
from src.infrastructure.library.mappers.chapter_mapper import ChapterMapper
from src.models import Book as BookORM
from src.models import Chapter as ChapterORM

logger = logging.getLogger(__name__)


class ChapterRepository:
    """Domain-centric repository for Chapter persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = ChapterMapper()

    def find_by_id(self, chapter_id: ChapterId, user_id: UserId) -> Chapter | None:
        """Find a chapter by ID with ownership verification."""
        stmt = (
            select(ChapterORM)
            .join(BookORM, BookORM.id == ChapterORM.book_id)
            .where(ChapterORM.id == chapter_id.value)
            .where(BookORM.user_id == user_id.value)
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_all_by_book(self, book_id: BookId, user_id: UserId) -> list[Chapter]:
        """Find all chapters for a book, ordered by chapter_number."""
        stmt = (
            select(ChapterORM)
            .join(BookORM, BookORM.id == ChapterORM.book_id)
            .where(BookORM.id == book_id.value)
            .where(BookORM.user_id == user_id.value)
            .order_by(ChapterORM.chapter_number)
        )
        orm_models = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(m) for m in orm_models]

    def get_by_numbers(
        self, book_id: BookId, chapter_numbers: set[int], user_id: UserId
    ) -> dict[int, Chapter]:
        """
        Get chapters by their numeric chapter_number.

        Returns dict mapping chapter_number → Chapter entity.
        Only includes chapters with non-null chapter_number.
        Used during highlight upload for efficient chapter association.
        """
        if not chapter_numbers:
            return {}

        stmt = (
            select(ChapterORM)
            .join(BookORM, BookORM.id == ChapterORM.book_id)
            .where(BookORM.id == book_id.value)
            .where(BookORM.user_id == user_id.value)
            .where(ChapterORM.chapter_number.in_(chapter_numbers))
            .where(ChapterORM.chapter_number.is_not(None))
        )

        orm_models = self.db.execute(stmt).scalars().all()

        # Map to dict by chapter_number
        result: dict[int, Chapter] = {}
        for orm_model in orm_models:
            if orm_model.chapter_number is not None:
                result[orm_model.chapter_number] = self.mapper.to_domain(orm_model)

        return result

    def _match_legacy_flat_chapter(
        self,
        name: str,
        chapter_by_name_and_parent: dict[tuple[str, int | None], ChapterORM],
        existing_chapter_keys: set[tuple[str, int | None]],
    ) -> ChapterORM | None:
        """Match a TOC chapter to a legacy flat chapter (parent_id=None) by name.

        Before hierarchical TOC support was added, chapters were stored without
        parent associations. When an EPUB is uploaded for a book with such legacy
        chapters, we need to match them by name alone to avoid creating duplicates
        and to preserve existing highlight foreign key references.

        This is migration-era logic that can be removed once all production books
        have been re-uploaded with hierarchical TOC data.
        """
        legacy_key = (name, None)
        if legacy_key in chapter_by_name_and_parent and legacy_key in existing_chapter_keys:
            chapter = chapter_by_name_and_parent[legacy_key]

            # If chapter does not have start point, it has to be legacy
            # TODO: Except if it is PDF, but those are not supported yet.
            if chapter.start_xpoint is None:
                return chapter

        return None

    def sync_chapters_from_toc(  # noqa: PLR0912
        self,
        book_id: BookId,
        user_id: UserId,
        chapters: list[tuple[str, int, str | None, str | None, str | None]],
    ) -> int:
        """
        Synchronize chapters from TOC data, creating new and updating existing chapters.

        This method handles bulk chapter creation/update from EPUB TOC parsing.
        It preserves hierarchical parent-child relationships and handles duplicates.

        Args:
            book_id: ID of the book
            user_id: ID of the user (for ownership verification)
            chapters: List of (chapter_name, chapter_number, parent_name, start_xpoint, end_xpoint) tuples

        Returns:
            Number of chapters created (not including updates)
        """
        if not chapters:
            return 0

        # Get existing chapters for this book by names
        chapter_names = {name for name, _, _, _, _ in chapters}

        stmt = (
            select(ChapterORM)
            .join(BookORM, BookORM.id == ChapterORM.book_id)
            .where(BookORM.id == book_id.value)
            .where(BookORM.user_id == user_id.value)
            .where(ChapterORM.name.in_(chapter_names))
        )
        existing_chapters_list = self.db.execute(stmt).scalars().all()

        # Build tracking dictionaries from existing chapters
        # chapter_by_name: for parent lookups
        # (last one wins if duplicate names - acceptable for parent resolution)
        # chapter_by_name_and_parent: for duplicate detection (unique key)
        # existing_chapter_keys: tracks which (name, parent_id) pairs came from DB
        chapter_by_name: dict[str, ChapterORM] = {}
        chapter_by_name_and_parent: dict[tuple[str, int | None], ChapterORM] = {}
        existing_chapter_keys: set[tuple[str, int | None]] = set()

        for ch in existing_chapters_list:
            chapter_by_name[ch.name] = ch
            key = (ch.name, ch.parent_id)
            chapter_by_name_and_parent[key] = ch
            existing_chapter_keys.add(key)

        chapters_to_update = []
        created_count = 0

        # Process chapters in order (parents before children due to sequential numbering)
        for name, chapter_number, parent_name, start_xpoint, end_xpoint in chapters:
            # Determine parent_id from parent_name
            parent_id = None
            if parent_name and parent_name in chapter_by_name:
                parent_id = chapter_by_name[parent_name].id

            # Check if chapter with this (name, parent_id) combination exists
            chapter_key = (name, parent_id)
            if chapter_key in chapter_by_name_and_parent:
                # This exact chapter (same name AND parent) already exists
                existing_chapter = chapter_by_name_and_parent[chapter_key]

                # Check if it needs updating (only if it came from DB)
                if chapter_key in existing_chapter_keys:
                    needs_update = False

                    if existing_chapter.chapter_number != chapter_number:
                        existing_chapter.chapter_number = chapter_number
                        needs_update = True

                    if existing_chapter.parent_id != parent_id:
                        existing_chapter.parent_id = parent_id
                        needs_update = True

                    if existing_chapter.start_xpoint != start_xpoint:
                        existing_chapter.start_xpoint = start_xpoint
                        needs_update = True

                    if existing_chapter.end_xpoint != end_xpoint:
                        existing_chapter.end_xpoint = end_xpoint
                        needs_update = True

                    if needs_update:
                        chapters_to_update.append(existing_chapter)
                else:
                    # True duplicate in ToC (same name and parent, already created in loop)
                    logger.warning(
                        f"Duplicate chapter '{name}' in ToC with same parent "
                        f"(parent_id={parent_id}). Skipping duplicate."
                    )
            else:
                # Check for legacy flat chapter to update instead of creating duplicate
                legacy_chapter = (
                    self._match_legacy_flat_chapter(
                        name,
                        chapter_by_name_and_parent,
                        existing_chapter_keys,
                    )
                    if parent_id is not None
                    else None
                )

                if legacy_chapter is not None:
                    legacy_key = (name, None)
                    legacy_chapter.parent_id = parent_id
                    legacy_chapter.chapter_number = chapter_number
                    legacy_chapter.start_xpoint = start_xpoint
                    legacy_chapter.end_xpoint = end_xpoint
                    chapters_to_update.append(legacy_chapter)

                    # Move tracking from old key to new key
                    del chapter_by_name_and_parent[legacy_key]
                    existing_chapter_keys.discard(legacy_key)
                    chapter_by_name_and_parent[chapter_key] = legacy_chapter
                    existing_chapter_keys.add(chapter_key)
                    chapter_by_name[name] = legacy_chapter
                else:
                    # Truly new chapter — create it
                    chapter = ChapterORM(
                        book_id=book_id.value,
                        name=name,
                        chapter_number=chapter_number,
                        parent_id=parent_id,
                        start_xpoint=start_xpoint,
                        end_xpoint=end_xpoint,
                    )
                    self.db.add(chapter)
                    self.db.commit()
                    self.db.refresh(chapter)

                    # Add to tracking dictionaries for subsequent parent lookups
                    chapter_by_name[name] = chapter
                    chapter_by_name_and_parent[chapter_key] = chapter
                    created_count += 1

        if chapters_to_update:
            self.db.commit()
            logger.info(f"Updated {len(chapters_to_update)} existing chapters")

        logger.info(
            f"Synced TOC for book {book_id.value}: created {created_count} chapters, "
            f"updated {len(chapters_to_update)} chapters"
        )
        return created_count
