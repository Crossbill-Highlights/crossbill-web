"""HighlightTag repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import models
from src.exceptions import CrossbillError

logger = logging.getLogger(__name__)


class HighlightTagRepository:
    """Repository for HighlightTag database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, tag_id: int) -> models.HighlightTag | None:
        """Get a highlight tag by its ID."""
        stmt = select(models.HighlightTag).where(models.HighlightTag.id == tag_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_book_and_name(self, book_id: int, name: str) -> models.HighlightTag | None:
        """Get a highlight tag by book ID and name."""
        stmt = select(models.HighlightTag).where(
            models.HighlightTag.book_id == book_id,
            models.HighlightTag.name == name,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_book_id(self, book_id: int) -> list[models.HighlightTag]:
        """
        Get all highlight tags for a book that have active associations with non-deleted highlights.

        Only returns tags that are currently associated with at least one non-deleted highlight.
        Filters out tags that are only associated with soft-deleted highlights.
        """
        stmt = (
            select(models.HighlightTag)
            .join(
                models.highlight_highlight_tags,
                models.HighlightTag.id == models.highlight_highlight_tags.c.highlight_tag_id,
            )
            .join(
                models.Highlight,
                models.highlight_highlight_tags.c.highlight_id == models.Highlight.id,
            )
            .where(
                models.HighlightTag.book_id == book_id,
                models.Highlight.deleted_at.is_(None),  # Only non-deleted highlights
            )
            .distinct()
            .order_by(models.HighlightTag.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, book_id: int, name: str) -> models.HighlightTag:
        """Create a new highlight tag."""
        tag = models.HighlightTag(book_id=book_id, name=name)
        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        logger.info(f"Created highlight tag: {tag.name} (id={tag.id}, book_id={book_id})")
        return tag

    def get_or_create(self, book_id: int, name: str) -> models.HighlightTag:
        """Get existing highlight tag by book and name or create a new one."""
        tag = self.get_by_book_and_name(book_id, name)
        if tag:
            return tag
        return self.create(book_id, name)

    def delete(self, tag_id: int) -> bool:
        """Delete a highlight tag by ID."""
        tag = self.get_by_id(tag_id)
        if not tag:
            return False
        self.db.delete(tag)
        self.db.flush()
        logger.info(f"Deleted highlight tag: {tag.name} (id={tag_id})")
        return True

    def update(self, tag_id: int, **kwargs: str | int | None) -> models.HighlightTag | None:
        """Update a highlight tag with the provided fields."""
        tag = self.get_by_id(tag_id)
        if not tag:
            return None

        for key, value in kwargs.items():
            if hasattr(tag, key):
                setattr(tag, key, value)

        self.db.flush()
        self.db.refresh(tag)
        logger.info(f"Updated highlight tag: {tag.name} (id={tag_id})")
        return tag

    # HighlightTagGroup methods

    def get_tag_group_by_id(self, tag_group_id: int) -> models.HighlightTagGroup | None:
        """Get a highlight tag group by its ID."""
        stmt = select(models.HighlightTagGroup).where(models.HighlightTagGroup.id == tag_group_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_tag_group_by_book_and_name(
        self, book_id: int, name: str
    ) -> models.HighlightTagGroup | None:
        """Get a highlight tag group by book ID and name."""
        stmt = select(models.HighlightTagGroup).where(
            models.HighlightTagGroup.book_id == book_id,
            models.HighlightTagGroup.name == name,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_tag_groups_by_book_id(self, book_id: int) -> list[models.HighlightTagGroup]:
        """Get all highlight tag groups for a book."""
        stmt = (
            select(models.HighlightTagGroup)
            .where(models.HighlightTagGroup.book_id == book_id)
            .order_by(models.HighlightTagGroup.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_tag_group(self, book_id: int, name: str) -> models.HighlightTagGroup:
        """Create a new highlight tag group.

        Raises:
            CrossbillError: If a tag group with the same name already exists for this book
        """
        tag_group = models.HighlightTagGroup(book_id=book_id, name=name)
        self.db.add(tag_group)
        try:
            self.db.flush()
        except IntegrityError as e:
            self.db.rollback()
            # Check if it's the unique constraint violation for tag group name
            error_msg = str(e).lower()
            if (
                "highlight_tag_groups.book_id" in error_msg
                and "highlight_tag_groups.name" in error_msg
            ):
                raise CrossbillError(
                    f"A tag group with the name '{name}' already exists for this book",
                    status_code=409,
                ) from e
            if "uq_highlight_tag_group_book_name" in error_msg:
                raise CrossbillError(
                    f"A tag group with the name '{name}' already exists for this book",
                    status_code=409,
                ) from e
            # Re-raise if it's a different integrity error
            raise

        self.db.refresh(tag_group)
        logger.info(
            f"Created highlight tag group: {tag_group.name} (id={tag_group.id}, book_id={book_id})"
        )
        return tag_group

    def update_tag_group(self, tag_group_id: int, name: str) -> models.HighlightTagGroup | None:
        """Update a highlight tag group's name.

        Raises:
            CrossbillError: If a tag group with the same name already exists for this book
        """
        tag_group = self.get_tag_group_by_id(tag_group_id)
        if not tag_group:
            return None

        tag_group.name = name
        try:
            self.db.flush()
        except IntegrityError as e:
            self.db.rollback()
            # Check if it's the unique constraint violation for tag group name
            error_msg = str(e).lower()
            if (
                "highlight_tag_groups.book_id" in error_msg
                and "highlight_tag_groups.name" in error_msg
            ):
                raise CrossbillError(
                    f"A tag group with the name '{name}' already exists for this book",
                    status_code=409,
                ) from e
            if "uq_highlight_tag_group_book_name" in error_msg:
                raise CrossbillError(
                    f"A tag group with the name '{name}' already exists for this book",
                    status_code=409,
                ) from e
            # Re-raise if it's a different integrity error
            raise

        self.db.refresh(tag_group)
        logger.info(f"Updated highlight tag group: {tag_group.name} (id={tag_group_id})")
        return tag_group

    def upsert_tag_group(
        self, book_id: int, name: str, tag_group_id: int | None = None
    ) -> models.HighlightTagGroup:
        """Create a new tag group or update existing one.

        Raises:
            CrossbillError: If creating a new tag group and one with the same name already exists
        """
        if tag_group_id:
            # Update existing tag group
            tag_group = self.update_tag_group(tag_group_id, name)
            if tag_group:
                return tag_group

        # When creating a new tag group, check if one with this name already exists
        # and raise an error instead of returning the existing one
        existing = self.get_tag_group_by_book_and_name(book_id, name)
        if existing:
            raise CrossbillError(
                f"A tag group with the name '{name}' already exists for this book", status_code=409
            )

        # Create new tag group
        return self.create_tag_group(book_id, name)

    def delete_tag_group(self, tag_group_id: int) -> bool:
        """Delete a highlight tag group by ID."""
        tag_group = self.get_tag_group_by_id(tag_group_id)
        if not tag_group:
            return False

        # Tags' foreign keys will be set to NULL due to ondelete="SET NULL"
        self.db.delete(tag_group)
        self.db.flush()
        logger.info(f"Deleted highlight tag group: {tag_group.name} (id={tag_group_id})")
        return True
