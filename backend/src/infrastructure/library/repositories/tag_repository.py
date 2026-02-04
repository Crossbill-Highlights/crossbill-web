"""Repository for Tag domain entity."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, TagId, UserId
from src.domain.library.entities.tag import Tag
from src.infrastructure.library.mappers.tag_mapper import TagMapper
from src.models import Book as BookORM
from src.models import Tag as TagORM


class TagRepository:
    """Repository for Tag domain entity."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = TagMapper()

    def _find_by_names(self, names: list[str], user_id: UserId) -> list[Tag]:
        """
        Get multiple tags by their names for a specific user in a single query.

        Args:
            names: List of tag names
            user_id: The user ID

        Returns:
            List of tag entities
        """
        if not names:
            return []

        stmt = select(TagORM).where(
            TagORM.name.in_(names),
            TagORM.user_id == user_id.value,
        )
        orm_models = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orm_models]

    def find_tags_for_book(self, book_id: BookId, user_id: UserId) -> list[Tag]:
        """
        Get all tags associated with a book.

        Args:
            book_id: The book ID
            user_id: The user ID

        Returns:
            List of tag entities
        """
        stmt = (
            select(TagORM)
            .join(BookORM.tags)
            .where(
                BookORM.id == book_id.value,
                BookORM.user_id == user_id.value,
            )
            .order_by(TagORM.name)
        )
        orm_models = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orm_models]

    def get_or_create_many(self, names: list[str], user_id: UserId) -> list[Tag]:
        """
        Get existing tags or create new ones for a list of names.

        Uses bulk operations to minimize database queries:
        1. Single query to fetch all existing tags by name
        2. Single bulk insert for new tags

        Args:
            names: List of tag names
            user_id: The user ID

        Returns:
            List of tag entities (mix of existing and newly created)
        """
        if not names:
            return []

        # Normalize names (strip whitespace, filter empty)
        normalized = [name.strip() for name in names if name.strip()]
        if not normalized:
            return []

        # Single query to get all existing tags
        existing_tags = self._find_by_names(normalized, user_id)
        existing_names = {tag.name for tag in existing_tags}

        # Find names that need to be created
        new_names = [name for name in normalized if name not in existing_names]

        # Bulk create new tags
        new_tags: list[Tag] = []
        if new_names:
            new_tag_orms = [TagORM(name=name, user_id=user_id.value) for name in new_names]
            self.db.add_all(new_tag_orms)
            self.db.flush()
            new_tags = [self.mapper.to_domain(orm) for orm in new_tag_orms]

        return existing_tags + new_tags

    # Book-tag association methods

    def add_tags_to_book(self, book_id: BookId, tag_ids: list[TagId], user_id: UserId) -> None:
        """
        Add tags to a book (manages the many-to-many association).

        Only adds tags that are not already associated with the book.

        Args:
            book_id: The book ID
            tag_ids: List of tag IDs to add
            user_id: The user ID for authorization check
        """
        if not tag_ids:
            return

        # Verify ownership and get ORM models
        book_orm = self.db.execute(
            select(BookORM).where(
                BookORM.id == book_id.value,
                BookORM.user_id == user_id.value,
            )
        ).scalar_one_or_none()

        if not book_orm:
            return

        # Get existing tag IDs to avoid duplicates
        existing_tag_ids = {tag.id for tag in book_orm.tags}

        # Fetch tag ORMs that aren't already associated
        tag_id_values = [tid.value for tid in tag_ids if tid.value not in existing_tag_ids]
        if not tag_id_values:
            return

        stmt = select(TagORM).where(
            TagORM.id.in_(tag_id_values),
            TagORM.user_id == user_id.value,
        )
        tag_orms = list(self.db.execute(stmt).scalars().all())

        # Add associations
        if tag_orms:
            book_orm.tags.extend(tag_orms)
            self.db.flush()

    def replace_book_tags(self, book_id: BookId, tag_ids: list[TagId], user_id: UserId) -> None:
        """
        Replace all tags on a book (manages the many-to-many association).

        Args:
            book_id: The book ID
            tag_ids: List of tag IDs (will replace all existing tags)
            user_id: The user ID for authorization check
        """
        # Verify ownership and get ORM model
        book_orm = self.db.execute(
            select(BookORM).where(
                BookORM.id == book_id.value,
                BookORM.user_id == user_id.value,
            )
        ).scalar_one_or_none()

        if not book_orm:
            return

        # Fetch tag ORMs
        if tag_ids:
            tag_id_values = [tid.value for tid in tag_ids]
            stmt = select(TagORM).where(
                TagORM.id.in_(tag_id_values),
                TagORM.user_id == user_id.value,
            )
            tag_orms = list(self.db.execute(stmt).scalars().all())
        else:
            tag_orms = []

        # Replace entire collection
        book_orm.tags = tag_orms
        self.db.flush()
