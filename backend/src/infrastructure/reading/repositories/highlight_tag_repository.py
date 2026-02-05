"""Repository for HighlightTag and HighlightTagGroup domain entities."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import (
    BookId,
    HighlightId,
    HighlightTagGroupId,
    HighlightTagId,
    UserId,
)
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.domain.reading.entities.highlight_tag_group import HighlightTagGroup
from src.infrastructure.reading.mappers.highlight_tag_group_mapper import (
    HighlightTagGroupMapper,
)
from src.infrastructure.reading.mappers.highlight_tag_mapper import HighlightTagMapper
from src.models import Highlight as HighlightORM
from src.models import HighlightTag as HighlightTagORM
from src.models import HighlightTagGroup as HighlightTagGroupORM
from src.models import highlight_highlight_tags


class HighlightTagRepository:
    """Repository for HighlightTag and HighlightTagGroup domain entities."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = HighlightTagMapper()
        self.group_mapper = HighlightTagGroupMapper()

    # Tag methods

    def find_by_id(self, tag_id: HighlightTagId, user_id: UserId) -> HighlightTag | None:
        """
        Find a tag by ID and user ID.

        Args:
            tag_id: The tag ID
            user_id: The user ID

        Returns:
            Tag entity if found, None otherwise
        """
        stmt = select(HighlightTagORM).where(
            HighlightTagORM.id == tag_id.value,
            HighlightTagORM.user_id == user_id.value,
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_by_book_and_name(
        self, book_id: BookId, name: str, user_id: UserId
    ) -> HighlightTag | None:
        """
        Find a tag by book, name, and user.

        Args:
            book_id: The book ID
            name: The tag name
            user_id: The user ID

        Returns:
            Tag entity if found, None otherwise
        """
        stmt = select(HighlightTagORM).where(
            HighlightTagORM.book_id == book_id.value,
            HighlightTagORM.name == name,
            HighlightTagORM.user_id == user_id.value,
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_by_book(self, book_id: BookId, user_id: UserId) -> list[HighlightTag]:
        """
        Get all tags for a book that have active highlight associations.

        This filters out tags that only have soft-deleted highlights.

        Args:
            book_id: The book ID
            user_id: The user ID

        Returns:
            List of tag entities
        """
        stmt = (
            select(HighlightTagORM)
            .join(highlight_highlight_tags)
            .join(HighlightORM)
            .where(
                HighlightTagORM.book_id == book_id.value,
                HighlightTagORM.user_id == user_id.value,
                HighlightORM.deleted_at.is_(None),
            )
            .distinct()
            .order_by(HighlightTagORM.name)
        )
        orm_models = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orm_models]

    def save(self, tag: HighlightTag) -> HighlightTag:
        """
        Save a tag entity.

        Args:
            tag: The tag entity to save

        Returns:
            Saved tag entity with updated ID
        """
        if tag.id.value == 0:
            # Create new
            orm_model = self.mapper.to_orm(tag)
            self.db.add(orm_model)
            self.db.commit()
            self.db.refresh(orm_model)
            return self.mapper.to_domain(orm_model)
        # Update existing
        stmt = select(HighlightTagORM).where(HighlightTagORM.id == tag.id.value)
        existing_orm = self.db.execute(stmt).scalar_one()
        self.mapper.to_orm(tag, existing_orm)
        self.db.commit()
        return self.mapper.to_domain(existing_orm)

    def delete(self, tag_id: HighlightTagId, user_id: UserId) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: The tag ID
            user_id: The user ID

        Returns:
            True if deleted, False if not found
        """
        tag_orm = self.db.execute(
            select(HighlightTagORM).where(
                HighlightTagORM.id == tag_id.value,
                HighlightTagORM.user_id == user_id.value,
            )
        ).scalar_one_or_none()

        if not tag_orm:
            return False

        self.db.delete(tag_orm)
        self.db.commit()
        return True

    # Tag group methods

    def find_groups_by_book(self, book_id: BookId) -> list[HighlightTagGroup]:
        """
        Find all tag groups for a book.

        Args:
            book_id: The book ID

        Returns:
            List of tag group entities, ordered by name
        """
        stmt = (
            select(HighlightTagGroupORM)
            .where(HighlightTagGroupORM.book_id == book_id.value)
            .order_by(HighlightTagGroupORM.name)
        )
        orm_models = self.db.execute(stmt).scalars().all()
        return [self.group_mapper.to_domain(orm) for orm in orm_models]

    def find_group_by_id(
        self, group_id: HighlightTagGroupId, book_id: BookId
    ) -> HighlightTagGroup | None:
        """
        Find a tag group by ID and book ID.

        Args:
            group_id: The group ID
            book_id: The book ID

        Returns:
            Group entity if found, None otherwise
        """
        stmt = select(HighlightTagGroupORM).where(
            HighlightTagGroupORM.id == group_id.value,
            HighlightTagGroupORM.book_id == book_id.value,
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.group_mapper.to_domain(orm_model) if orm_model else None

    def find_group_by_name(self, book_id: BookId, name: str) -> HighlightTagGroup | None:
        """
        Find a tag group by book and name.

        Args:
            book_id: The book ID
            name: The group name

        Returns:
            Group entity if found, None otherwise
        """
        stmt = select(HighlightTagGroupORM).where(
            HighlightTagGroupORM.book_id == book_id.value,
            HighlightTagGroupORM.name == name,
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.group_mapper.to_domain(orm_model) if orm_model else None

    def save_group(self, group: HighlightTagGroup) -> HighlightTagGroup:
        """
        Save a tag group entity.

        Args:
            group: The group entity to save

        Returns:
            Saved group entity with updated ID
        """
        if group.id.value == 0:
            # Create new
            orm_model = self.group_mapper.to_orm(group)
            self.db.add(orm_model)
            self.db.commit()
            self.db.refresh(orm_model)
            return self.group_mapper.to_domain(orm_model)
        # Update existing
        stmt = select(HighlightTagGroupORM).where(HighlightTagGroupORM.id == group.id.value)
        existing_orm = self.db.execute(stmt).scalar_one()
        self.group_mapper.to_orm(group, existing_orm)
        self.db.commit()
        return self.group_mapper.to_domain(existing_orm)

    def delete_group(self, group_id: HighlightTagGroupId) -> bool:
        """
        Delete a tag group.

        Args:
            group_id: The group ID

        Returns:
            True if deleted, False if not found
        """
        group_orm = self.db.execute(
            select(HighlightTagGroupORM).where(HighlightTagGroupORM.id == group_id.value)
        ).scalar_one_or_none()

        if not group_orm:
            return False

        self.db.delete(group_orm)
        self.db.commit()
        return True

    # Tag-Highlight association methods

    def add_tag_to_highlight(
        self, highlight_id: HighlightId, tag_id: HighlightTagId, user_id: UserId
    ) -> bool:
        """
        Add a tag to a highlight (manages the many-to-many association).

        Args:
            highlight_id: The highlight ID
            tag_id: The tag ID
            user_id: The user ID for authorization check

        Returns:
            True if added, False if already associated or not found
        """
        # Verify ownership and get ORM models
        highlight_orm = self.db.execute(
            select(HighlightORM).where(
                HighlightORM.id == highlight_id.value,
                HighlightORM.user_id == user_id.value,
            )
        ).scalar_one_or_none()

        tag_orm = self.db.execute(
            select(HighlightTagORM).where(
                HighlightTagORM.id == tag_id.value,
                HighlightTagORM.user_id == user_id.value,
            )
        ).scalar_one_or_none()

        if not highlight_orm or not tag_orm:
            return False

        # Add association if not already present
        if tag_orm not in highlight_orm.highlight_tags:
            highlight_orm.highlight_tags.append(tag_orm)
            self.db.commit()
            return True

        return False

    def remove_tag_from_highlight(
        self, highlight_id: HighlightId, tag_id: HighlightTagId, user_id: UserId
    ) -> bool:
        """
        Remove a tag from a highlight (removes the many-to-many association).

        Args:
            highlight_id: The highlight ID
            tag_id: The tag ID
            user_id: The user ID for authorization check

        Returns:
            True if removed, False if not found or not associated
        """
        # Verify ownership and get ORM models
        highlight_orm = self.db.execute(
            select(HighlightORM).where(
                HighlightORM.id == highlight_id.value,
                HighlightORM.user_id == user_id.value,
            )
        ).scalar_one_or_none()

        tag_orm = self.db.execute(
            select(HighlightTagORM).where(
                HighlightTagORM.id == tag_id.value,
                HighlightTagORM.user_id == user_id.value,
            )
        ).scalar_one_or_none()

        if not highlight_orm or not tag_orm:
            return False

        # Remove association if present
        if tag_orm in highlight_orm.highlight_tags:
            highlight_orm.highlight_tags.remove(tag_orm)
            self.db.commit()
            return True

        return False

    def check_group_exists(self, group_id: HighlightTagGroupId) -> bool:
        """
        Check if a tag group exists (regardless of book).

        Args:
            group_id: The group ID

        Returns:
            True if the group exists, False otherwise
        """
        stmt = select(HighlightTagGroupORM.id).where(HighlightTagGroupORM.id == group_id.value)
        result = self.db.execute(stmt).scalar_one_or_none()
        return result is not None
