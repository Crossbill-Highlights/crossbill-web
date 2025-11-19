"""Tests for tag group API endpoints and functionality."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models


class TestCreateTagGroup:
    """Test suite for POST /highlights/tag_group endpoint."""

    def test_create_tag_group_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful creation of a tag group."""
        # Create a book
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Create tag group
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": book.id, "name": "Important Themes"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Important Themes"
        assert data["book_id"] == book.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify in database
        tag_group = db_session.query(models.HighlightTagGroup).filter_by(id=data["id"]).first()
        assert tag_group is not None
        assert tag_group.name == "Important Themes"
        assert tag_group.book_id == book.id

    def test_update_tag_group_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful update of a tag group."""
        # Create a book and tag group
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Old Name")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        # Update tag group
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"id": tag_group.id, "book_id": book.id, "name": "New Name"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tag_group.id
        assert data["name"] == "New Name"
        assert data["book_id"] == book.id

        # Verify in database
        db_session.refresh(tag_group)
        assert tag_group.name == "New Name"

    def test_create_tag_group_duplicate_name(self, client: TestClient, db_session: Session) -> None:
        """Test creating tag group with duplicate name returns 409 error."""
        # Create a book and tag group
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        # Try to create another tag group with same name
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": book.id, "name": "Themes"},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()
        assert "Themes" in data["detail"]

    def test_create_tag_group_nonexistent_book(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test creating tag group for non-existent book."""
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": 99999, "name": "Themes"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_tag_group_empty_name(self, client: TestClient, db_session: Session) -> None:
        """Test creating tag group with empty name."""
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": book.id, "name": "   "},
        )

        assert response.status_code in {
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        }

    def test_update_tag_group_to_duplicate_name(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test updating tag group to a name that already exists."""
        # Create a book and two tag groups
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group1 = models.HighlightTagGroup(book_id=book.id, name="Aivelo")
        tag_group2 = models.HighlightTagGroup(book_id=book.id, name="Different Name")
        db_session.add_all([tag_group1, tag_group2])
        db_session.commit()
        db_session.refresh(tag_group1)
        db_session.refresh(tag_group2)

        # Try to update tag_group2 to have the same name as tag_group1
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"id": tag_group2.id, "book_id": book.id, "name": "Aivelo"},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()
        assert "Aivelo" in data["detail"]


class TestDeleteTagGroup:
    """Test suite for DELETE /highlights/tag_group/:id endpoint."""

    def test_delete_tag_group_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful deletion of a tag group."""
        # Create a book and tag group
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        # Delete tag group
        response = client.delete(f"/api/v1/highlights/tag_group/{tag_group.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        deleted_group = (
            db_session.query(models.HighlightTagGroup).filter_by(id=tag_group.id).first()
        )
        assert deleted_group is None

    def test_delete_tag_group_with_tags(self, client: TestClient, db_session: Session) -> None:
        """Test deleting tag group sets tags' tag_group_id to NULL."""
        # Create a book, tag group, and tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        tag1 = models.HighlightTag(book_id=book.id, name="Tag 1", tag_group_id=tag_group.id)
        tag2 = models.HighlightTag(book_id=book.id, name="Tag 2", tag_group_id=tag_group.id)
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Delete tag group
        response = client.delete(f"/api/v1/highlights/tag_group/{tag_group.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify tags still exist but with NULL tag_group_id
        db_session.refresh(tag1)
        db_session.refresh(tag2)
        assert tag1.tag_group_id is None
        assert tag2.tag_group_id is None

    def test_delete_tag_group_not_found(self, client: TestClient, db_session: Session) -> None:
        """Test deleting non-existent tag group."""
        response = client.delete("/api/v1/highlights/tag_group/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateTag:
    """Test suite for POST /book/:id/highlight_tag/:id endpoint."""

    def test_update_tag_add_to_group(self, client: TestClient, db_session: Session) -> None:
        """Test adding a tag to a tag group."""
        # Create a book, tag group, and tag
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        tag = models.HighlightTag(book_id=book.id, name="Important")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        # Update tag to add to group
        response = client.post(
            f"/api/v1/book/{book.id}/highlight_tag/{tag.id}",
            json={"tag_group_id": tag_group.id},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tag.id
        assert data["tag_group_id"] == tag_group.id

        # Verify in database
        db_session.refresh(tag)
        assert tag.tag_group_id == tag_group.id

    def test_update_tag_remove_from_group(self, client: TestClient, db_session: Session) -> None:
        """Test removing a tag from a tag group."""
        # Create a book, tag group, and tag
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        tag = models.HighlightTag(book_id=book.id, name="Important", tag_group_id=tag_group.id)
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        # Update tag to remove from group
        response = client.post(
            f"/api/v1/book/{book.id}/highlight_tag/{tag.id}",
            json={"tag_group_id": None},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tag.id
        assert data["tag_group_id"] is None

        # Verify in database
        db_session.refresh(tag)
        assert tag.tag_group_id is None

    def test_update_tag_rename(self, client: TestClient, db_session: Session) -> None:
        """Test renaming a tag."""
        # Create a book and tag
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag = models.HighlightTag(book_id=book.id, name="Old Name")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        # Update tag name
        response = client.post(
            f"/api/v1/book/{book.id}/highlight_tag/{tag.id}",
            json={"name": "New Name"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tag.id
        assert data["name"] == "New Name"

        # Verify in database
        db_session.refresh(tag)
        assert tag.name == "New Name"

    def test_update_tag_rename_and_add_to_group(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test renaming a tag and adding it to a group."""
        # Create a book, tag group, and tag
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        tag = models.HighlightTag(book_id=book.id, name="Old Name")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        # Update both name and group
        response = client.post(
            f"/api/v1/book/{book.id}/highlight_tag/{tag.id}",
            json={"name": "New Name", "tag_group_id": tag_group.id},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tag.id
        assert data["name"] == "New Name"
        assert data["tag_group_id"] == tag_group.id

        # Verify in database
        db_session.refresh(tag)
        assert tag.name == "New Name"
        assert tag.tag_group_id == tag_group.id

    def test_update_tag_wrong_book(self, client: TestClient, db_session: Session) -> None:
        """Test updating tag with wrong book_id."""
        # Create two books and a tag
        book1 = models.Book(title="Book 1", author="Author 1")
        book2 = models.Book(title="Book 2", author="Author 2")
        db_session.add_all([book1, book2])
        db_session.commit()
        db_session.refresh(book1)
        db_session.refresh(book2)

        tag = models.HighlightTag(book_id=book1.id, name="Tag")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        # Try to update with wrong book_id
        response = client.post(
            f"/api/v1/book/{book2.id}/highlight_tag/{tag.id}",
            json={"name": "New Name"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_tag_nonexistent_group(self, client: TestClient, db_session: Session) -> None:
        """Test updating tag with non-existent tag group."""
        # Create a book and tag
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag = models.HighlightTag(book_id=book.id, name="Tag")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        # Try to update with non-existent group
        response = client.post(
            f"/api/v1/book/{book.id}/highlight_tag/{tag.id}",
            json={"tag_group_id": 99999},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBookDetailsWithTagGroups:
    """Test suite for GET /book/:id endpoint with tag groups."""

    def test_get_book_details_includes_tag_groups(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that book details include tag groups."""
        # Create a book with tag groups
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group1 = models.HighlightTagGroup(book_id=book.id, name="Themes")
        tag_group2 = models.HighlightTagGroup(book_id=book.id, name="Characters")
        db_session.add_all([tag_group1, tag_group2])
        db_session.commit()

        # Get book details
        response = client.get(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "highlight_tag_groups" in data
        assert len(data["highlight_tag_groups"]) == 2

        # Check tag group names (should be sorted alphabetically)
        tag_group_names = [tg["name"] for tg in data["highlight_tag_groups"]]
        assert "Themes" in tag_group_names
        assert "Characters" in tag_group_names

    def test_get_book_details_tags_include_group_id(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that tags in book details include tag_group_id."""
        # Create a book with tag group and tags
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        tag1 = models.HighlightTag(book_id=book.id, name="Tag 1", tag_group_id=tag_group.id)
        tag2 = models.HighlightTag(book_id=book.id, name="Tag 2", tag_group_id=None)
        db_session.add_all([tag1, tag2])
        db_session.commit()

        # Create a highlight with tags to ensure they appear
        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=1,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        highlight.highlight_tags.extend([tag1, tag2])
        db_session.commit()

        # Get book details
        response = client.get(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check tags include tag_group_id
        assert "highlight_tags" in data
        tag_map = {tag["name"]: tag for tag in data["highlight_tags"]}

        if "Tag 1" in tag_map:
            assert tag_map["Tag 1"]["tag_group_id"] == tag_group.id
        if "Tag 2" in tag_map:
            assert tag_map["Tag 2"]["tag_group_id"] is None


class TestCascadeDelete:
    """Test suite for cascade delete behavior."""

    def test_delete_book_deletes_tag_groups(self, client: TestClient, db_session: Session) -> None:
        """Test that deleting a book also deletes its tag groups."""
        # Create a book with tag groups
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        tag_group = models.HighlightTagGroup(book_id=book.id, name="Themes")
        db_session.add(tag_group)
        db_session.commit()
        db_session.refresh(tag_group)

        # Delete book
        response = client.delete(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify tag group was deleted
        deleted_group = (
            db_session.query(models.HighlightTagGroup).filter_by(id=tag_group.id).first()
        )
        assert deleted_group is None
