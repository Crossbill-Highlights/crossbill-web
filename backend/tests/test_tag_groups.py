"""Tests for tag group API endpoints and functionality."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models
from tests.conftest import create_test_book, create_test_highlight


class TestCreateTagGroup:
    """Test suite for POST /highlights/tag_group endpoint."""

    def test_create_tag_group_success(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test successful creation of a tag group."""
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": test_book.id, "name": "Important Themes"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Important Themes"
        assert data["book_id"] == test_book.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify in database
        tag_group = db_session.query(models.HighlightTagGroup).filter_by(id=data["id"]).first()
        assert tag_group is not None
        assert tag_group.name == "Important Themes"
        assert tag_group.book_id == test_book.id

    def test_update_tag_group_success(
        self, client: TestClient, db_session: Session, test_tag_group: models.HighlightTagGroup
    ) -> None:
        """Test successful update of a tag group."""
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={
                "id": test_tag_group.id,
                "book_id": test_tag_group.book_id,
                "name": "New Name",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_tag_group.id
        assert data["name"] == "New Name"
        assert data["book_id"] == test_tag_group.book_id

        # Verify in database
        db_session.refresh(test_tag_group)
        assert test_tag_group.name == "New Name"

    def test_create_tag_group_duplicate_name(
        self, client: TestClient, test_tag_group: models.HighlightTagGroup
    ) -> None:
        """Test creating tag group with duplicate name returns 409 error."""
        # Try to create another tag group with same name
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": test_tag_group.book_id, "name": test_tag_group.name},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()
        assert test_tag_group.name in data["detail"]

    def test_create_tag_group_nonexistent_book(self, client: TestClient) -> None:
        """Test creating tag group for non-existent book."""
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": 99999, "name": "Themes"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_tag_group_empty_name(self, client: TestClient, test_book: models.Book) -> None:
        """Test creating tag group with empty name."""
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"book_id": test_book.id, "name": "   "},
        )

        assert response.status_code in {
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        }

    def test_update_tag_group_to_duplicate_name(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_tag_group: models.HighlightTagGroup,
    ) -> None:
        """Test updating tag group to a name that already exists."""
        # Create a second tag group
        tag_group2 = models.HighlightTagGroup(book_id=test_book.id, name="Different Name")
        db_session.add(tag_group2)
        db_session.commit()
        db_session.refresh(tag_group2)

        # Try to update tag_group2 to have the same name as test_tag_group
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"id": tag_group2.id, "book_id": test_book.id, "name": test_tag_group.name},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()
        assert test_tag_group.name in data["detail"]

    def test_update_tag_group_wrong_book(
        self,
        client: TestClient,
        db_session: Session,
        test_tag_group: models.HighlightTagGroup,
        test_user: models.User,
    ) -> None:
        """Test updating tag group with mismatched book_id."""
        # Create a second book
        book2 = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Book 2",
            author="Author 2",
        )

        # Try to update test_tag_group with book2's id (should fail)
        response = client.post(
            "/api/v1/highlights/tag_group",
            json={"id": test_tag_group.id, "book_id": book2.id, "name": "Updated Name"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "does not belong to book" in data["detail"].lower()


class TestDeleteTagGroup:
    """Test suite for DELETE /highlights/tag_group/:id endpoint."""

    def test_delete_tag_group_success(
        self, client: TestClient, db_session: Session, test_tag_group: models.HighlightTagGroup
    ) -> None:
        """Test successful deletion of a tag group."""
        tag_group_id = test_tag_group.id

        response = client.delete(f"/api/v1/highlights/tag_group/{tag_group_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        deleted_group = (
            db_session.query(models.HighlightTagGroup).filter_by(id=tag_group_id).first()
        )
        assert deleted_group is None

    def test_delete_tag_group_with_tags(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_tag_group: models.HighlightTagGroup,
        test_user: models.User,
    ) -> None:
        """Test deleting tag group sets tags' tag_group_id to NULL."""
        # Create tags associated with the tag group
        tag1 = models.HighlightTag(
            book_id=test_book.id,
            user_id=test_user.id,
            name="Tag 1",
            tag_group_id=test_tag_group.id,
        )
        tag2 = models.HighlightTag(
            book_id=test_book.id,
            user_id=test_user.id,
            name="Tag 2",
            tag_group_id=test_tag_group.id,
        )
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Delete tag group
        response = client.delete(f"/api/v1/highlights/tag_group/{test_tag_group.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify tags still exist but with NULL tag_group_id
        db_session.refresh(tag1)
        db_session.refresh(tag2)
        assert tag1.tag_group_id is None
        assert tag2.tag_group_id is None

    def test_delete_tag_group_not_found(self, client: TestClient) -> None:
        """Test deleting non-existent tag group."""
        response = client.delete("/api/v1/highlights/tag_group/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateTag:
    """Test suite for POST /books/:id/highlight_tag/:id endpoint."""

    def test_update_tag_add_to_group(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_tag_group: models.HighlightTagGroup,
        test_highlight_tag: models.HighlightTag,
    ) -> None:
        """Test adding a tag to a tag group."""
        response = client.post(
            f"/api/v1/books/{test_book.id}/highlight_tag/{test_highlight_tag.id}",
            json={"tag_group_id": test_tag_group.id},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_highlight_tag.id
        assert data["tag_group_id"] == test_tag_group.id

        # Verify in database
        db_session.refresh(test_highlight_tag)
        assert test_highlight_tag.tag_group_id == test_tag_group.id

    def test_update_tag_remove_from_group(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_tag_group: models.HighlightTagGroup,
        test_user: models.User,
    ) -> None:
        """Test removing a tag from a tag group."""
        # Create a tag that's already in a group
        tag = models.HighlightTag(
            book_id=test_book.id,
            user_id=test_user.id,
            name="Important",
            tag_group_id=test_tag_group.id,
        )
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        # Update tag to remove from group
        response = client.post(
            f"/api/v1/books/{test_book.id}/highlight_tag/{tag.id}",
            json={"tag_group_id": None},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tag.id
        assert data["tag_group_id"] is None

        # Verify in database
        db_session.refresh(tag)
        assert tag.tag_group_id is None

    def test_update_tag_rename(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_highlight_tag: models.HighlightTag,
    ) -> None:
        """Test renaming a tag."""
        response = client.post(
            f"/api/v1/books/{test_book.id}/highlight_tag/{test_highlight_tag.id}",
            json={"name": "New Name"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_highlight_tag.id
        assert data["name"] == "New Name"

        # Verify in database
        db_session.refresh(test_highlight_tag)
        assert test_highlight_tag.name == "New Name"

    def test_update_tag_rename_and_add_to_group(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_tag_group: models.HighlightTagGroup,
        test_highlight_tag: models.HighlightTag,
    ) -> None:
        """Test renaming a tag and adding it to a group."""
        response = client.post(
            f"/api/v1/books/{test_book.id}/highlight_tag/{test_highlight_tag.id}",
            json={"name": "New Name", "tag_group_id": test_tag_group.id},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_highlight_tag.id
        assert data["name"] == "New Name"
        assert data["tag_group_id"] == test_tag_group.id

        # Verify in database
        db_session.refresh(test_highlight_tag)
        assert test_highlight_tag.name == "New Name"
        assert test_highlight_tag.tag_group_id == test_tag_group.id

    def test_update_tag_wrong_book(
        self,
        client: TestClient,
        db_session: Session,
        test_highlight_tag: models.HighlightTag,
        test_user: models.User,
    ) -> None:
        """Test updating tag with wrong book_id."""
        # Create a second book
        book2 = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Book 2",
            author="Author 2",
        )

        # Try to update with wrong book_id
        response = client.post(
            f"/api/v1/books/{book2.id}/highlight_tag/{test_highlight_tag.id}",
            json={"name": "New Name"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_tag_nonexistent_group(
        self, client: TestClient, test_book: models.Book, test_highlight_tag: models.HighlightTag
    ) -> None:
        """Test updating tag with non-existent tag group."""
        response = client.post(
            f"/api/v1/books/{test_book.id}/highlight_tag/{test_highlight_tag.id}",
            json={"tag_group_id": 99999},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBookDetailsWithTagGroups:
    """Test suite for GET /books/:id endpoint with tag groups."""

    def test_get_book_details_includes_tag_groups(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
    ) -> None:
        """Test that book details include tag groups."""
        # Create tag groups
        tag_group1 = models.HighlightTagGroup(book_id=test_book.id, name="Themes")
        tag_group2 = models.HighlightTagGroup(book_id=test_book.id, name="Characters")
        db_session.add_all([tag_group1, tag_group2])
        db_session.commit()

        # Get book details
        response = client.get(f"/api/v1/books/{test_book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "highlight_tag_groups" in data
        assert len(data["highlight_tag_groups"]) == 2

        # Check tag group names (should be sorted alphabetically)
        tag_group_names = [tg["name"] for tg in data["highlight_tag_groups"]]
        assert "Themes" in tag_group_names
        assert "Characters" in tag_group_names

    def test_get_book_details_tags_include_group_id(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_tag_group: models.HighlightTagGroup,
        test_user: models.User,
    ) -> None:
        """Test that tags in book details include tag_group_id."""
        # Create tags
        tag1 = models.HighlightTag(
            book_id=test_book.id,
            user_id=test_user.id,
            name="Tag 1",
            tag_group_id=test_tag_group.id,
        )
        tag2 = models.HighlightTag(
            book_id=test_book.id, user_id=test_user.id, name="Tag 2", tag_group_id=None
        )
        db_session.add_all([tag1, tag2])
        db_session.commit()

        # Create a highlight with tags to ensure they appear
        highlight = create_test_highlight(
            db_session=db_session,
            book=test_book,
            user_id=test_user.id,
            text="Test highlight",
            page=1,
            datetime_str="2024-01-15 14:30:22",
        )

        highlight.highlight_tags.extend([tag1, tag2])
        db_session.commit()

        # Get book details
        response = client.get(f"/api/v1/books/{test_book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check tags include tag_group_id
        assert "highlight_tags" in data
        tag_map = {tag["name"]: tag for tag in data["highlight_tags"]}

        if "Tag 1" in tag_map:
            assert tag_map["Tag 1"]["tag_group_id"] == test_tag_group.id
        if "Tag 2" in tag_map:
            assert tag_map["Tag 2"]["tag_group_id"] is None


class TestCascadeDelete:
    """Test suite for cascade delete behavior."""

    def test_delete_book_deletes_tag_groups(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_tag_group: models.HighlightTagGroup,
    ) -> None:
        """Test that deleting a book also deletes its tag groups."""
        tag_group_id = test_tag_group.id

        # Delete book
        response = client.delete(f"/api/v1/books/{test_book.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify tag group was deleted
        deleted_group = (
            db_session.query(models.HighlightTagGroup).filter_by(id=tag_group_id).first()
        )
        assert deleted_group is None
