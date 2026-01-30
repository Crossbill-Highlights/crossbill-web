"""
Domain-centric repository for Highlight aggregate.

Returns domain entities instead of ORM models.
Uses HighlightMapper internally for conversions.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.domain.common.value_objects import BookId, ContentHash, HighlightId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.domain.library.entities.book import Book
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.infrastructure.learning.mappers.flashcard_mapper import FlashcardMapper
from src.infrastructure.library.mappers.book_mapper import BookMapper
from src.infrastructure.library.mappers.chapter_mapper import ChapterMapper
from src.infrastructure.reading.mappers.highlight_mapper import HighlightMapper
from src.infrastructure.reading.mappers.highlight_tag_mapper import HighlightTagMapper
from src.models import Highlight as HighlightORM


class HighlightRepository:
    """Repository for Highlight persistence (domain-centric)."""

    def __init__(self, db: Session) -> None:
        """
        Initialize repository.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.mapper = HighlightMapper()
        self.book_mapper = BookMapper()
        self.chapter_mapper = ChapterMapper()
        self.highlight_tag_mapper = HighlightTagMapper()
        self.flashcard_mapper = FlashcardMapper()

    def find_by_id(self, highlight_id: HighlightId, user_id: UserId) -> Highlight | None:
        """
        Load highlight by ID.

        Args:
            highlight_id: Highlight ID to find
            user_id: User ID for authorization check

        Returns:
            Highlight domain entity if found, None otherwise
        """
        stmt = (
            select(HighlightORM)
            .where(HighlightORM.id == highlight_id.value)
            .where(HighlightORM.user_id == user_id.value)
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()

        if not orm_model:
            return None

        return self.mapper.to_domain(orm_model)

    def find_by_id_with_relations(
        self, highlight_id: HighlightId, user_id: UserId
    ) -> tuple[Highlight, list[Flashcard], list[HighlightTag]] | None:
        """
        Load highlight by ID with its flashcards and tags eagerly loaded.

        Args:
            highlight_id: Highlight ID to find
            user_id: User ID for authorization check

        Returns:
            Tuple of (Highlight, list[Flashcard], list[HighlightTag]) if found, None otherwise
        """
        stmt = (
            select(HighlightORM)
            .options(
                joinedload(HighlightORM.flashcards),
                joinedload(HighlightORM.highlight_tags),
            )
            .where(HighlightORM.id == highlight_id.value)
            .where(HighlightORM.user_id == user_id.value)
        )
        orm_model = self.db.execute(stmt).unique().scalar_one_or_none()

        if not orm_model:
            return None

        highlight = self.mapper.to_domain(orm_model)
        flashcards = [self.flashcard_mapper.to_domain(fc_orm) for fc_orm in orm_model.flashcards]
        highlight_tags = [
            self.highlight_tag_mapper.to_domain(tag_orm) for tag_orm in orm_model.highlight_tags
        ]

        return highlight, flashcards, highlight_tags

    def save(self, highlight: Highlight) -> Highlight:
        """
        Persist highlight to database.

        If highlight has placeholder ID (0), creates new record and returns with real ID.
        Otherwise updates existing record.

        Args:
            highlight: Highlight domain entity to save

        Returns:
            Highlight with updated ID from database
        """
        if highlight.id.value == 0:
            # Create new highlight
            orm_model = self.mapper.to_orm(highlight)
            self.db.add(orm_model)
            self.db.flush()  # Get ID without committing

            # Return domain entity with real ID
            return self.mapper.to_domain(orm_model)
        # Update existing highlight
        stmt = select(HighlightORM).where(HighlightORM.id == highlight.id.value)
        existing_orm = self.db.execute(stmt).scalar_one()

        # Update ORM model using mapper
        self.mapper.to_orm(highlight, existing_orm)
        self.db.flush()

        return self.mapper.to_domain(existing_orm)

    def get_existing_hashes(
        self, user_id: UserId, book_id: BookId, hashes: list[ContentHash]
    ) -> set[ContentHash]:
        """
        Check which content hashes already exist for a user.

        Efficient deduplication check using unique constraint index.
        Includes both active and soft-deleted highlights to prevent
        recreating highlights that were previously deleted by the user.

        Args:
            user_id: User to check for
            book_id: Book containing the highlight
            hashes: List of ContentHash value objects to check

        Returns:
            Set of ContentHash value objects that already exist (including soft-deleted)
        """
        if not hashes:
            return set()

        # Convert value objects to strings for query
        hash_strings = [h.value for h in hashes]

        stmt = (
            select(HighlightORM.content_hash)
            .where(HighlightORM.user_id == user_id.value)
            .where(HighlightORM.book_id == book_id.value)
            .where(HighlightORM.content_hash.in_(hash_strings))
            # Include soft-deleted highlights to prevent recreation
        )

        result = self.db.execute(stmt).scalars().all()

        # Convert back to value objects
        return {ContentHash(hash_str) for hash_str in result}

    def bulk_save(self, highlights: list[Highlight]) -> list[Highlight]:
        """
        Bulk save highlights efficiently.

        All highlights must have placeholder IDs (new highlights).

        Args:
            highlights: List of new Highlight domain entities

        Returns:
            List of highlights with updated IDs from database
        """
        if not highlights:
            return []

        # Convert all to ORM models
        orm_models = [self.mapper.to_orm(h) for h in highlights]

        # Bulk insert
        self.db.bulk_save_objects(orm_models, return_defaults=True)
        self.db.flush()

        # Convert back to domain entities with real IDs
        return [self.mapper.to_domain(orm) for orm in orm_models]

    def search(
        self,
        search_text: str,
        user_id: UserId,
        book_id: BookId | None = None,
        limit: int = 100,
    ) -> list[tuple[Highlight, Book, Chapter | None, list[HighlightTag]]]:
        """
        Search for highlights using full-text search (PostgreSQL) or LIKE (SQLite).

        Returns highlights with their associated book, chapter, and tags eagerly loaded.

        Args:
            search_text: Text to search for
            user_id: User ID for filtering highlights
            book_id: Optional book ID to filter by
            limit: Maximum number of results to return (default 100)

        Returns:
            List of tuples containing (Highlight entity, Book entity, Chapter entity or None, list[HighlightTag])
        """
        # Check database type
        is_postgresql = self.db.bind is not None and self.db.bind.dialect.name == "postgresql"

        # Build the base query with eager loading of relationships
        stmt = (
            select(HighlightORM)
            .options(
                joinedload(HighlightORM.book),
                joinedload(HighlightORM.chapter),
                joinedload(HighlightORM.highlight_tags),
            )
            .where(
                HighlightORM.user_id == user_id.value,
                HighlightORM.deleted_at.is_(None),
            )
        )

        if is_postgresql:
            # PostgreSQL: Use full-text search
            search_query = func.plainto_tsquery("english", search_text)
            stmt = stmt.where(HighlightORM.text_search_vector.op("@@")(search_query))
        else:
            # SQLite: Use LIKE-based search
            stmt = stmt.where(HighlightORM.text.ilike(f"%{search_text}%"))

        # Add optional book_id filter
        if book_id is not None:
            stmt = stmt.where(HighlightORM.book_id == book_id.value)

        # Order by relevance and limit results
        if is_postgresql:
            search_query = func.plainto_tsquery("english", search_text)
            stmt = stmt.order_by(func.ts_rank(HighlightORM.text_search_vector, search_query).desc())
        else:
            # SQLite: Order by created_at (newest first)
            stmt = stmt.order_by(HighlightORM.created_at.desc())

        stmt = stmt.limit(limit)

        # Execute query
        results = self.db.execute(stmt).scalars().all()

        # Convert ORM models to domain entities
        return [
            (
                self.mapper.to_domain(highlight_orm),
                self.book_mapper.to_domain(highlight_orm.book),
                self.chapter_mapper.to_domain(highlight_orm.chapter)
                if highlight_orm.chapter
                else None,
                [
                    self.highlight_tag_mapper.to_domain(tag_orm)
                    for tag_orm in highlight_orm.highlight_tags
                ],
            )
            for highlight_orm in results
        ]
