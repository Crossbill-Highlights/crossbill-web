"""Tests for EPUB ToC chapter creation and update logic.

This test suite focuses on the complex logic in EpubService._save_chapters_from_toc,
which handles:
- Creating new chapters from ToC
- Updating existing chapters
- Handling hierarchical parent-child relationships
- Managing duplicate chapter names (same name under different parents)
- Detecting true duplicates (same name and parent in ToC)
"""

# type: ignore - Testing protected methods and accessing DB fields that Pyright doesn't recognize

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src import models
from src.services.epub_service import EpubService
from tests.conftest import create_test_book


@pytest.fixture
def epub_service(db_session: Session) -> EpubService:
    """Create an EpubService instance with test database session."""
    return EpubService(db=db_session)


@pytest.fixture
def test_book_for_toc(db_session: Session) -> models.Book:
    """Create a test book for ToC testing."""
    return create_test_book(
        db_session=db_session,
        user_id=1,
        title="ToC Test Book",
        author="Test Author",
    )


class TestSimpleChapterCreation:
    """Test basic chapter creation without hierarchy."""

    def test_create_single_chapter(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ) -> None:
        """Test creating a single chapter from ToC."""
        chapters: list[tuple[str, int, str | None]] = [("Introduction", 1, None)]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 1
        db_chapters = db_session.query(models.Chapter).filter_by(book_id=test_book_for_toc.id).all()
        assert len(db_chapters) == 1
        assert db_chapters[0].name == "Introduction"
        assert db_chapters[0].chapter_number == 1
        assert db_chapters[0].parent_id is None

    def test_create_multiple_chapters(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test creating multiple chapters from ToC."""
        chapters: list[tuple[str, int, str | None]] = [
            ("Chapter 1", 1, None),
            ("Chapter 2", 2, None),
            ("Chapter 3", 3, None),
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 3
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )
        assert len(db_chapters) == 3
        assert [ch.name for ch in db_chapters] == ["Chapter 1", "Chapter 2", "Chapter 3"]
        assert all(ch.parent_id is None for ch in db_chapters)

    def test_empty_chapters_list(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test handling empty chapters list."""
        chapters: list[tuple[str, int, str | None]] = []

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 0
        db_chapters = db_session.query(models.Chapter).filter_by(book_id=test_book_for_toc.id).all()
        assert len(db_chapters) == 0


class TestHierarchicalChapters:
    """Test hierarchical parent-child chapter relationships."""

    def test_simple_parent_child(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test creating parent chapter with child chapters."""
        chapters: list[tuple[str, int, str | None]] = [
            ("Part I", 1, None),
            ("Chapter 1", 2, "Part I"),
            ("Chapter 2", 3, "Part I"),
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 3
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )
        assert len(db_chapters) == 3

        part1 = db_chapters[0]
        chapter1 = db_chapters[1]
        chapter2 = db_chapters[2]

        assert part1.name == "Part I"
        assert part1.parent_id is None

        assert chapter1.name == "Chapter 1"
        assert chapter1.parent_id == part1.id

        assert chapter2.name == "Chapter 2"
        assert chapter2.parent_id == part1.id

    def test_multiple_parent_levels(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test creating multiple levels of parent-child hierarchy."""
        chapters: list[tuple[str, int, str | None]] = [
            ("Part I", 1, None),
            ("Chapter 1", 2, "Part I"),
            ("Section 1.1", 3, "Chapter 1"),
            ("Section 1.2", 4, "Chapter 1"),
            ("Chapter 2", 5, "Part I"),
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 5
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )

        part1, chapter1, section11, section12, chapter2 = db_chapters

        assert part1.parent_id is None
        assert chapter1.parent_id == part1.id
        assert section11.parent_id == chapter1.id
        assert section12.parent_id == chapter1.id
        assert chapter2.parent_id == part1.id


class TestDuplicateChapterNames:
    """Test handling chapters with duplicate names.

    With the constraint (book_id, parent_id, name), chapters can have the same name
    as long as they have different parents.
    """

    def test_duplicate_names_different_parents_allowed(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test that chapters with same name under different parents are both created.

        This is the main bug fix - "Harjoitukset" under Part I and Part II should
        both be created as separate chapters.
        """
        chapters: list[tuple[str, int, str | None]] = [
            ("Part I", 1, None),
            ("Harjoitukset", 2, "Part I"),  # Exercises for Part I
            ("Part II", 3, None),
            ("Harjoitukset", 4, "Part II"),  # Exercises for Part II
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 4
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )
        assert len(db_chapters) == 4

        part1, harjoitukset1, part2, harjoitukset2 = db_chapters

        # Both "Harjoitukset" chapters should exist
        assert harjoitukset1.name == "Harjoitukset"
        assert harjoitukset1.parent_id == part1.id
        assert harjoitukset1.chapter_number == 2

        assert harjoitukset2.name == "Harjoitukset"
        assert harjoitukset2.parent_id == part2.id
        assert harjoitukset2.chapter_number == 4

        # They should have different IDs
        assert harjoitukset1.id != harjoitukset2.id

    def test_duplicate_names_at_root_level_skipped(
        self,
        epub_service: EpubService,
        test_book_for_toc: models.Book,
        db_session: Session,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that duplicate root-level chapters (both parent_id=None) are skipped.

        With the (book_id, parent_id, name) constraint, two root chapters with same name
        have the same (name, parent_id) key, so they're treated as duplicates.
        """
        chapters: list[tuple[str, int, str | None]] = [
            ("Preface", 1, None),
            ("Preface", 2, None),  # Duplicate at root level
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        # Only one created, duplicate skipped
        assert created_count == 1
        db_chapters = db_session.query(models.Chapter).filter_by(book_id=test_book_for_toc.id).all()
        assert len(db_chapters) == 1
        assert db_chapters[0].name == "Preface"
        assert db_chapters[0].parent_id is None

        # Should log a warning about the duplicate
        assert "Duplicate chapter 'Preface' in ToC with same parent" in caplog.text

    def test_true_duplicate_in_toc_skipped(
        self,
        epub_service: EpubService,
        test_book_for_toc: models.Book,
        db_session: Session,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that true duplicates (same name and parent in ToC) are skipped.

        This would indicate a malformed ToC where the same chapter appears twice
        under the same parent.
        """
        chapters: list[tuple[str, int, str | None]] = [
            ("Part I", 1, None),
            ("Chapter 1", 2, "Part I"),
            ("Chapter 1", 3, "Part I"),  # True duplicate - same name and parent
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        # Only 2 chapters created (duplicate skipped)
        assert created_count == 2
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )
        assert len(db_chapters) == 2
        assert db_chapters[0].name == "Part I"
        assert db_chapters[1].name == "Chapter 1"

        # Should log a warning about the duplicate
        assert "Duplicate chapter 'Chapter 1' in ToC with same parent" in caplog.text


class TestUpdatingExistingChapters:
    """Test updating existing chapters when re-uploading ToC."""

    def test_update_chapter_number(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test updating chapter_number for existing chapter."""
        # Create initial chapter
        existing_chapter = models.Chapter(
            book_id=test_book_for_toc.id,
            name="Chapter 1",
            chapter_number=1,
            parent_id=None,
        )
        db_session.add(existing_chapter)
        db_session.commit()
        chapter_id = existing_chapter.id

        # Re-upload with different chapter number
        chapters: list[tuple[str, int, str | None]] = [("Chapter 1", 5, None)]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 0  # No new chapters created
        db_session.refresh(existing_chapter)
        assert existing_chapter.id == chapter_id  # Same chapter
        assert existing_chapter.chapter_number == 5  # Updated

    def test_update_parent_id(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test updating parent_id for existing chapter when they share the same parent.

        NOTE: This only works when the parent_id doesn't change. If parent_id changes,
        the unique key (book_id, parent_id, name) changes, and the current logic
        creates a new chapter instead of updating. This is a known limitation.
        """
        # Create initial chapters with the same parent
        parent = models.Chapter(
            book_id=test_book_for_toc.id, name="Part I", chapter_number=1, parent_id=None
        )
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)

        child = models.Chapter(
            book_id=test_book_for_toc.id,
            name="Chapter 1",
            chapter_number=2,
            parent_id=parent.id,  # Initially HAS parent
        )
        db_session.add(child)
        db_session.commit()
        child_id = child.id

        # Re-upload with same parent but different chapter number
        chapters: list[tuple[str, int, str | None]] = [
            ("Part I", 1, None),
            ("Chapter 1", 5, "Part I"),  # Same parent, different number
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 0  # No new chapters
        db_session.refresh(child)
        assert child.id == child_id  # Same chapter
        assert child.parent_id == parent.id  # Parent unchanged
        assert child.chapter_number == 5  # Updated

    def test_mixed_create_and_update(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test creating new chapters while updating existing ones."""
        # Create initial chapter
        existing = models.Chapter(
            book_id=test_book_for_toc.id,
            name="Chapter 1",
            chapter_number=1,
            parent_id=None,
        )
        db_session.add(existing)
        db_session.commit()
        existing_id = existing.id

        # Upload with existing chapter (different number) and new chapters
        chapters: list[tuple[str, int, str | None]] = [
            ("Chapter 1", 5, None),  # Exists - update
            ("Chapter 2", 6, None),  # New - create
            ("Chapter 3", 7, None),  # New - create
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 2  # Only new chapters counted
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )
        assert len(db_chapters) == 3
        assert db_chapters[0].id == existing_id  # Same chapter
        assert db_chapters[0].chapter_number == 5  # Updated


class TestEdgeCases:
    """Test edge cases and potential issues in the ToC logic."""

    def test_duplicate_parent_names_correct_assignment(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test that duplicate parent names work correctly with the fixed logic.

        This test verifies that when two parent chapters have the same name
        (e.g., "Introduction" under Part I and "Introduction" under Part II),
        child chapters are assigned to the correct parent.

        With the chapter_by_name_and_parent tracking, this edge case is handled correctly.
        The child chapters reference the correct parent even though multiple parents
        have the same name.

        Example:
            Part I
              Introduction (id=10)
                Chapter 1 (should have parent_id=10) ✓
            Part II
              Introduction (id=20)
                Chapter 1 (should have parent_id=20) ✓
        """
        chapters: list[tuple[str, int, str | None]] = [
            ("Part I", 1, None),
            ("Introduction", 2, "Part I"),
            ("Chapter 1", 3, "Introduction"),  # Should have parent_id = Introduction under Part I
            ("Part II", 4, None),
            ("Introduction", 5, "Part II"),  # Same name as chapter 2
            (
                "Chapter 1",
                6,
                "Introduction",
            ),  # Should have parent_id = Introduction under Part II
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 6
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )

        part1, intro1, chapter1_under_intro1, part2, intro2, chapter1_under_intro2 = db_chapters

        # Verify parent structure
        assert intro1.name == "Introduction"
        assert intro1.parent_id == part1.id

        assert intro2.name == "Introduction"
        assert intro2.parent_id == part2.id

        # Verify children are correctly assigned to their respective parents
        # Chapter 1 (number 3) should have intro1 as parent
        assert chapter1_under_intro1.parent_id == intro1.id

        # Chapter 1 (number 6) should have intro2 as parent
        assert chapter1_under_intro2.parent_id == intro2.id

    def test_parent_referenced_before_definition(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test that parent chapters must come before children in ToC.

        This tests the assumption that ToC is ordered (parents before children).
        If a child references a parent that hasn't been processed yet, parent_id
        will be None.
        """
        chapters: list[tuple[str, int, str | None]] = [
            ("Chapter 1", 1, "Part I"),  # References parent that doesn't exist yet
            ("Part I", 2, None),  # Parent comes after
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 2
        db_chapters = (
            db_session.query(models.Chapter)
            .filter_by(book_id=test_book_for_toc.id)
            .order_by(models.Chapter.chapter_number)
            .all()
        )

        chapter1, part1 = db_chapters

        # Chapter 1 won't have parent_id set because Part I wasn't processed yet
        assert chapter1.parent_id is None
        assert part1.parent_id is None

    def test_nonexistent_parent_name(
        self, epub_service: EpubService, test_book_for_toc: models.Book, db_session: Session
    ):
        """Test handling of parent_name that doesn't exist in ToC."""
        chapters: list[tuple[str, int, str | None]] = [
            ("Chapter 1", 1, "Part I"),  # References parent that never appears
        ]

        created_count = epub_service._save_chapters_from_toc(
            book_id=test_book_for_toc.id, user_id=1, chapters=chapters
        )

        assert created_count == 1
        db_chapters = db_session.query(models.Chapter).filter_by(book_id=test_book_for_toc.id).all()
        assert len(db_chapters) == 1
        # Parent doesn't exist, so parent_id is None
        assert db_chapters[0].parent_id is None
