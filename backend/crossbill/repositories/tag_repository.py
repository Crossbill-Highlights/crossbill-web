"""Tag repository for database operations."""

import logging
from datetime import UTC, datetime

from sqlalchemy import and_, delete, select, update
from sqlalchemy.orm import Session

from crossbill import models

logger = logging.getLogger(__name__)


class TagRepository:
    """Repository for Tag database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_name(self, name: str) -> models.Tag | None:
        """Get a tag by its name."""
        stmt = select(models.Tag).where(models.Tag.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, tag_id: int) -> models.Tag | None:
        """Get a tag by its ID."""
        stmt = select(models.Tag).where(models.Tag.id == tag_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, name: str) -> models.Tag:
        """Create a new tag."""
        tag = models.Tag(name=name)
        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        logger.info(f"Created tag: {tag.name} (id={tag.id})")
        return tag

    def get_or_create(self, name: str) -> models.Tag:
        """Get existing tag by name or create a new one."""
        tag = self.get_by_name(name)
        if tag:
            return tag
        return self.create(name)

    def get_all(self) -> list[models.Tag]:
        """Get all tags."""
        stmt = select(models.Tag).order_by(models.Tag.name)
        return list(self.db.execute(stmt).scalars().all())

    def add_tag_to_book(self, book_id: int, tag_id: int) -> None:
        """
        Add a tag to a book or restore it if soft-deleted.

        If the tag association already exists and is soft-deleted, it will be restored
        by setting deleted_at to NULL.

        Args:
            book_id: ID of the book
            tag_id: ID of the tag
        """
        # Check if association exists (including soft-deleted ones)
        stmt = select(models.book_tags).where(
            and_(
                models.book_tags.c.book_id == book_id,
                models.book_tags.c.tag_id == tag_id,
            )
        )
        existing = self.db.execute(stmt).fetchone()

        if existing:
            # If it exists and is soft-deleted, restore it
            if existing.deleted_at is not None:
                update_stmt = (
                    update(models.book_tags)
                    .where(
                        and_(
                            models.book_tags.c.book_id == book_id,
                            models.book_tags.c.tag_id == tag_id,
                        )
                    )
                    .values(deleted_at=None)
                )
                self.db.execute(update_stmt)
                self.db.flush()
                logger.info(f"Restored soft-deleted tag {tag_id} for book {book_id}")
        else:
            # Create new association
            insert_stmt = models.book_tags.insert().values(
                book_id=book_id,
                tag_id=tag_id,
            )
            self.db.execute(insert_stmt)
            self.db.flush()
            logger.info(f"Added tag {tag_id} to book {book_id}")

    def soft_delete_tag_from_book(self, book_id: int, tag_id: int) -> bool:
        """
        Soft delete a tag association from a book.

        Args:
            book_id: ID of the book
            tag_id: ID of the tag

        Returns:
            bool: True if the association was soft-deleted, False if it didn't exist or was already deleted
        """
        # Check if association exists and is not soft-deleted
        stmt = select(models.book_tags).where(
            and_(
                models.book_tags.c.book_id == book_id,
                models.book_tags.c.tag_id == tag_id,
                models.book_tags.c.deleted_at.is_(None),
            )
        )
        existing = self.db.execute(stmt).fetchone()

        if not existing:
            return False

        # Soft delete the association
        update_stmt = (
            update(models.book_tags)
            .where(
                and_(
                    models.book_tags.c.book_id == book_id,
                    models.book_tags.c.tag_id == tag_id,
                )
            )
            .values(deleted_at=datetime.now(UTC))
        )
        self.db.execute(update_stmt)
        self.db.flush()
        logger.info(f"Soft deleted tag {tag_id} from book {book_id}")
        return True

    def get_active_tags_for_book(self, book_id: int) -> list[models.Tag]:
        """
        Get all active (non-soft-deleted) tags for a book.

        Args:
            book_id: ID of the book

        Returns:
            list[Tag]: List of active tags for the book
        """
        stmt = (
            select(models.Tag)
            .join(models.book_tags, models.Tag.id == models.book_tags.c.tag_id)
            .where(
                and_(
                    models.book_tags.c.book_id == book_id,
                    models.book_tags.c.deleted_at.is_(None),
                )
            )
            .order_by(models.Tag.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def remove_all_tags_from_book_except(self, book_id: int, tag_ids: list[int]) -> None:
        """
        Soft delete all tags from a book except the ones in the provided list.

        This is used when updating a book's tags - tags not in the new list are soft-deleted.

        Args:
            book_id: ID of the book
            tag_ids: List of tag IDs to keep (all others will be soft-deleted)
        """
        # Soft delete all associations for this book that are not in the tag_ids list
        # and are not already soft-deleted
        if tag_ids:
            update_stmt = (
                update(models.book_tags)
                .where(
                    and_(
                        models.book_tags.c.book_id == book_id,
                        models.book_tags.c.tag_id.notin_(tag_ids),
                        models.book_tags.c.deleted_at.is_(None),
                    )
                )
                .values(deleted_at=datetime.now(UTC))
            )
        else:
            # If tag_ids is empty, soft delete all tags for this book
            update_stmt = (
                update(models.book_tags)
                .where(
                    and_(
                        models.book_tags.c.book_id == book_id,
                        models.book_tags.c.deleted_at.is_(None),
                    )
                )
                .values(deleted_at=datetime.now(UTC))
            )

        self.db.execute(update_stmt)
        self.db.flush()
        logger.info(f"Soft deleted tags for book {book_id} except {tag_ids}")
