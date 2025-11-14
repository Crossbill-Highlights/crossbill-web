"""Tests for tag soft deletion functionality."""

from datetime import UTC, datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from crossbill import models


class TestTagSoftDeleteInHighlightUpload:
    """Test suite for tag soft deletion during highlight upload."""

    def test_upload_with_tags_creates_tags(self, client: TestClient, db_session: Session) -> None:
        """Test that uploading highlights with tags creates tag associations."""
        payload = {
            "book": {
                "title": "Test Book",
                "author": "Test Author",
                "tags": ["Fiction", "Sci-Fi"],
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        book_id = data["book_id"]

        # Verify tags were created and associated
        book = db_session.query(models.Book).filter_by(id=book_id).first()
        assert book is not None
        assert len(book.tags) == 2
        tag_names = {tag.name for tag in book.tags}
        assert tag_names == {"Fiction", "Sci-Fi"}

        # Verify associations are not soft-deleted
        stmt = select(models.book_tags).where(models.book_tags.c.book_id == book_id)
        associations = db_session.execute(stmt).fetchall()
        assert len(associations) == 2
        for assoc in associations:
            assert assoc.deleted_at is None

    def test_upload_does_not_restore_soft_deleted_tags(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that uploading from KOReader does not restore soft-deleted tags."""
        # Create a book with tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Create tags
        tag1 = models.Tag(name="Fiction")
        tag2 = models.Tag(name="Sci-Fi")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Add both tags to book
        insert_stmt1 = models.book_tags.insert().values(book_id=book.id, tag_id=tag1.id)
        insert_stmt2 = models.book_tags.insert().values(book_id=book.id, tag_id=tag2.id)
        db_session.execute(insert_stmt1)
        db_session.execute(insert_stmt2)
        db_session.commit()

        # Soft delete "Sci-Fi" tag
        from sqlalchemy import update

        update_stmt = (
            update(models.book_tags)
            .where(
                and_(
                    models.book_tags.c.book_id == book.id,
                    models.book_tags.c.tag_id == tag2.id,
                )
            )
            .values(deleted_at=datetime.now(UTC))
        )
        db_session.execute(update_stmt)
        db_session.commit()

        # Upload from KOReader with both tags (simulating KOReader sending tags again)
        payload = {
            "book": {
                "title": "Test Book",
                "author": "Test Author",
                "tags": ["Fiction", "Sci-Fi"],  # Includes the soft-deleted tag
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK

        # Verify "Sci-Fi" tag is still soft-deleted (NOT restored)
        stmt = select(models.book_tags).where(
            and_(
                models.book_tags.c.book_id == book.id,
                models.book_tags.c.tag_id == tag2.id,
            )
        )
        assoc = db_session.execute(stmt).fetchone()
        assert assoc is not None
        assert assoc.deleted_at is not None  # Still soft-deleted

        # Verify book.tags only returns the non-deleted tag
        db_session.refresh(book)
        assert len(book.tags) == 1
        assert book.tags[0].name == "Fiction"

    def test_upload_removes_tags_not_in_request(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that uploading with fewer tags soft-deletes the missing ones."""
        # Create a book with tags via initial upload
        payload = {
            "book": {
                "title": "Test Book",
                "author": "Test Author",
                "tags": ["Fiction", "Sci-Fi", "Adventure"],
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK
        book_id = response.json()["book_id"]

        # Verify all tags are present
        book = db_session.query(models.Book).filter_by(id=book_id).first()
        assert len(book.tags) == 3

        # Upload again with only 2 tags
        payload["book"]["tags"] = ["Fiction", "Adventure"]
        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # Verify only 2 tags are active, and "Sci-Fi" is soft-deleted
        db_session.refresh(book)
        assert len(book.tags) == 2
        tag_names = {tag.name for tag in book.tags}
        assert tag_names == {"Fiction", "Adventure"}

        # Verify "Sci-Fi" association is soft-deleted
        sci_fi_tag = db_session.query(models.Tag).filter_by(name="Sci-Fi").first()
        assert sci_fi_tag is not None
        stmt = select(models.book_tags).where(
            and_(
                models.book_tags.c.book_id == book_id,
                models.book_tags.c.tag_id == sci_fi_tag.id,
            )
        )
        assoc = db_session.execute(stmt).fetchone()
        assert assoc is not None
        assert assoc.deleted_at is not None

    def test_upload_with_empty_tags_soft_deletes_all(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that uploading with no tags soft-deletes all existing tags."""
        # Create a book with tags
        payload = {
            "book": {
                "title": "Test Book",
                "author": "Test Author",
                "tags": ["Fiction", "Sci-Fi"],
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK
        book_id = response.json()["book_id"]

        # Upload again with empty tags
        payload["book"]["tags"] = []
        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # Verify all tags are soft-deleted
        book = db_session.query(models.Book).filter_by(id=book_id).first()
        assert len(book.tags) == 0

        # Verify associations are soft-deleted in database
        stmt = select(models.book_tags).where(models.book_tags.c.book_id == book_id)
        associations = db_session.execute(stmt).fetchall()
        assert len(associations) == 2  # Still exist in DB
        for assoc in associations:
            assert assoc.deleted_at is not None  # But are soft-deleted


class TestTagSoftDeleteInBookUpdate:
    """Test suite for tag soft deletion during book update via POST /api/v1/book/:id."""

    def test_update_tags_restores_soft_deleted(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that updating tags via UI restores soft-deleted tags."""
        # Create a book with tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Create and add tags
        tag1 = models.Tag(name="Fiction")
        tag2 = models.Tag(name="Sci-Fi")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Add both tags to book
        insert_stmt1 = models.book_tags.insert().values(book_id=book.id, tag_id=tag1.id)
        insert_stmt2 = models.book_tags.insert().values(book_id=book.id, tag_id=tag2.id)
        db_session.execute(insert_stmt1)
        db_session.execute(insert_stmt2)
        db_session.commit()

        # Soft delete "Sci-Fi" tag
        from sqlalchemy import update

        update_stmt = (
            update(models.book_tags)
            .where(
                and_(
                    models.book_tags.c.book_id == book.id,
                    models.book_tags.c.tag_id == tag2.id,
                )
            )
            .values(deleted_at=datetime.now(UTC))
        )
        db_session.execute(update_stmt)
        db_session.commit()

        # Verify only Fiction is active
        db_session.refresh(book)
        assert len(book.tags) == 1
        assert book.tags[0].name == "Fiction"

        # Update tags via UI to include Sci-Fi again
        payload = {"tags": ["Fiction", "Sci-Fi"]}
        response = client.post(f"/api/v1/book/{book.id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        tag_names = {tag["name"] for tag in data["tags"]}
        assert tag_names == {"Fiction", "Sci-Fi"}

        # Verify Sci-Fi association is restored (deleted_at is None)
        stmt = select(models.book_tags).where(
            and_(
                models.book_tags.c.book_id == book.id,
                models.book_tags.c.tag_id == tag2.id,
            )
        )
        assoc = db_session.execute(stmt).fetchone()
        assert assoc is not None
        assert assoc.deleted_at is None  # Restored!

    def test_update_tags_soft_deletes_removed_tags(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that updating tags soft-deletes tags not in the new list."""
        # Create a book with tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Add a highlight so we can get the book count
        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()

        # Create and add tags
        tag1 = models.Tag(name="Fiction")
        tag2 = models.Tag(name="Sci-Fi")
        tag3 = models.Tag(name="Adventure")
        db_session.add_all([tag1, tag2, tag3])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)
        db_session.refresh(tag3)

        # Add all tags to book
        for tag in [tag1, tag2, tag3]:
            insert_stmt = models.book_tags.insert().values(book_id=book.id, tag_id=tag.id)
            db_session.execute(insert_stmt)
        db_session.commit()

        # Verify all tags are active
        db_session.refresh(book)
        assert len(book.tags) == 3

        # Update tags to only include Fiction and Adventure
        payload = {"tags": ["Fiction", "Adventure"]}
        response = client.post(f"/api/v1/book/{book.id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        tag_names = {tag["name"] for tag in data["tags"]}
        assert tag_names == {"Fiction", "Adventure"}

        # Verify Sci-Fi is soft-deleted
        stmt = select(models.book_tags).where(
            and_(
                models.book_tags.c.book_id == book.id,
                models.book_tags.c.tag_id == tag2.id,
            )
        )
        assoc = db_session.execute(stmt).fetchone()
        assert assoc is not None
        assert assoc.deleted_at is not None

    def test_update_tags_with_empty_list_soft_deletes_all(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that updating with empty tag list soft-deletes all tags."""
        # Create a book with tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Add a highlight
        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()

        # Create and add tags
        tag1 = models.Tag(name="Fiction")
        tag2 = models.Tag(name="Sci-Fi")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Add tags to book
        for tag in [tag1, tag2]:
            insert_stmt = models.book_tags.insert().values(book_id=book.id, tag_id=tag.id)
            db_session.execute(insert_stmt)
        db_session.commit()

        # Update with empty tags
        payload = {"tags": []}
        response = client.post(f"/api/v1/book/{book.id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["tags"]) == 0

        # Verify all associations are soft-deleted
        stmt = select(models.book_tags).where(models.book_tags.c.book_id == book.id)
        associations = db_session.execute(stmt).fetchall()
        assert len(associations) == 2
        for assoc in associations:
            assert assoc.deleted_at is not None

    def test_book_list_excludes_soft_deleted_tags(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that GET /api/v1/highlights/books excludes soft-deleted tags."""
        # Create a book with tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Add a highlight
        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()

        # Create and add tags
        tag1 = models.Tag(name="Fiction")
        tag2 = models.Tag(name="Sci-Fi")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Add tags to book
        for tag in [tag1, tag2]:
            insert_stmt = models.book_tags.insert().values(book_id=book.id, tag_id=tag.id)
            db_session.execute(insert_stmt)
        db_session.commit()

        # Soft delete tag2
        from sqlalchemy import update

        update_stmt = (
            update(models.book_tags)
            .where(
                and_(
                    models.book_tags.c.book_id == book.id,
                    models.book_tags.c.tag_id == tag2.id,
                )
            )
            .values(deleted_at=datetime.now(UTC))
        )
        db_session.execute(update_stmt)
        db_session.commit()

        # Get books list
        response = client.get("/api/v1/highlights/books")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["books"]) == 1
        book_data = data["books"][0]
        assert len(book_data["tags"]) == 1
        assert book_data["tags"][0]["name"] == "Fiction"

    def test_book_details_excludes_soft_deleted_tags(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that GET /api/v1/book/:id excludes soft-deleted tags."""
        # Create a book with tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Create chapter and highlight
        chapter = models.Chapter(book_id=book.id, name="Chapter 1")
        db_session.add(chapter)
        db_session.commit()
        db_session.refresh(chapter)

        highlight = models.Highlight(
            book_id=book.id,
            chapter_id=chapter.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()

        # Create and add tags
        tag1 = models.Tag(name="Fiction")
        tag2 = models.Tag(name="Sci-Fi")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Add tags to book
        for tag in [tag1, tag2]:
            insert_stmt = models.book_tags.insert().values(book_id=book.id, tag_id=tag.id)
            db_session.execute(insert_stmt)
        db_session.commit()

        # Soft delete tag2
        from sqlalchemy import update

        update_stmt = (
            update(models.book_tags)
            .where(
                and_(
                    models.book_tags.c.book_id == book.id,
                    models.book_tags.c.tag_id == tag2.id,
                )
            )
            .values(deleted_at=datetime.now(UTC))
        )
        db_session.execute(update_stmt)
        db_session.commit()

        # Get book details
        response = client.get(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "Fiction"
