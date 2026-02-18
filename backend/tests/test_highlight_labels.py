"""Integration tests for highlight labels feature."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models
from src.infrastructure.library.schemas import EreaderBookMetadata
from tests.conftest import create_test_book, create_test_highlight, create_test_highlight_style

# Default user ID used by services (matches conftest default user)
DEFAULT_USER_ID = 1

# Type alias for the book creation fixture
CreateBookFunc = Callable[[dict[str, Any]], EreaderBookMetadata]


@pytest.fixture
def create_book_via_api(client: TestClient) -> CreateBookFunc:
    """Fixture factory for creating books via the API endpoint."""

    def _create_book(book_data: dict[str, Any]) -> EreaderBookMetadata:
        response = client.post("/api/v1/ereader/books", json=book_data)
        assert response.status_code == status.HTTP_200_OK
        return EreaderBookMetadata(**response.json())

    return _create_book


class TestHighlightUploadCreatesStyles:
    """Test that uploading highlights creates highlight_style rows."""

    def test_upload_with_color_and_drawer_creates_style(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that uploading highlights with color and drawer creates highlight style rows."""
        create_book_via_api(
            {
                "client_book_id": "test-labels-book",
                "title": "Labels Test Book",
                "author": "Test Author",
            }
        )

        payload = {
            "client_book_id": "test-labels-book",
            "highlights": [
                {
                    "text": "Yellow highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:30:22",
                    "color": "yellow",
                    "drawer": "lighten",
                },
                {
                    "text": "Green highlight",
                    "page": 20,
                    "datetime": "2024-01-15 15:00:00",
                    "color": "green",
                    "drawer": "lighten",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["highlights_created"] == 2

        # Verify highlight_style rows were created
        book = db_session.query(models.Book).filter_by(title="Labels Test Book").first()
        assert book is not None

        styles = db_session.query(models.HighlightStyle).filter_by(book_id=book.id).all()
        assert len(styles) == 2

        style_combos = {(s.device_color, s.device_style) for s in styles}
        assert ("yellow", "lighten") in style_combos
        assert ("green", "lighten") in style_combos

    def test_upload_duplicate_color_drawer_reuses_style(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that uploading highlights with same color+drawer reuses the same style."""
        create_book_via_api(
            {
                "client_book_id": "test-dedup-styles",
                "title": "Style Dedup Book",
                "author": "Test Author",
            }
        )

        payload = {
            "client_book_id": "test-dedup-styles",
            "highlights": [
                {
                    "text": "First yellow highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:00:00",
                    "color": "yellow",
                    "drawer": "lighten",
                },
                {
                    "text": "Second yellow highlight",
                    "page": 20,
                    "datetime": "2024-01-15 15:00:00",
                    "color": "yellow",
                    "drawer": "lighten",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["highlights_created"] == 2

        book = db_session.query(models.Book).filter_by(title="Style Dedup Book").first()
        assert book is not None

        # Only one style row should exist for (yellow, lighten)
        styles = db_session.query(models.HighlightStyle).filter_by(book_id=book.id).all()
        assert len(styles) == 1
        assert styles[0].device_color == "yellow"
        assert styles[0].device_style == "lighten"

        # Both highlights should reference the same style
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 2
        assert highlights[0].highlight_style_id == styles[0].id
        assert highlights[1].highlight_style_id == styles[0].id

    def test_highlight_response_includes_highlight_style_id(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that highlight responses include highlight_style_id field."""
        create_book_via_api(
            {
                "client_book_id": "test-style-response",
                "title": "Style Response Book",
                "author": "Test Author",
            }
        )

        # Upload a highlight with color/drawer
        payload = {
            "client_book_id": "test-style-response",
            "highlights": [
                {
                    "text": "Styled highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:00:00",
                    "color": "gray",
                    "drawer": "lighten",
                },
            ],
        }
        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # Get book details and check highlight_style_id is in the response
        book = db_session.query(models.Book).filter_by(title="Style Response Book").first()
        assert book is not None

        # Create a chapter so the highlight shows up in book details
        chapter = models.Chapter(book_id=book.id, name="Uncategorized")
        db_session.add(chapter)
        db_session.commit()
        db_session.refresh(chapter)

        # Associate highlight with chapter
        highlight = db_session.query(models.Highlight).filter_by(book_id=book.id).first()
        assert highlight is not None
        highlight.chapter_id = chapter.id
        db_session.commit()

        response = client.get(f"/api/v1/books/{book.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["chapters"]) == 1
        assert len(data["chapters"][0]["highlights"]) == 1
        h_data = data["chapters"][0]["highlights"][0]
        assert "label" in h_data
        assert h_data["label"] is not None
        assert "highlight_style_id" in h_data["label"]
        assert h_data["label"]["highlight_style_id"] is not None


class TestGetBookHighlightLabels:
    """Test GET /api/v1/books/{book_id}/highlight-labels endpoint."""

    def test_get_book_labels_returns_styles(self, client: TestClient, db_session: Session) -> None:
        """Test that book highlight labels endpoint returns styles with counts."""
        book = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Labels Book",
            author="Test Author",
        )

        # Create a highlight style
        style = create_test_highlight_style(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            book_id=book.id,
            device_color="yellow",
            device_style="lighten",
            label="Important",
        )

        # Create highlights that reference this style
        create_test_highlight(
            db_session=db_session,
            book=book,
            user_id=DEFAULT_USER_ID,
            text="Highlight A",
            datetime_str="2024-01-15 14:00:00",
            highlight_style_id=style.id,
        )
        create_test_highlight(
            db_session=db_session,
            book=book,
            user_id=DEFAULT_USER_ID,
            text="Highlight B",
            datetime_str="2024-01-15 15:00:00",
            highlight_style_id=style.id,
        )

        response = client.get(f"/api/v1/books/{book.id}/highlight-labels")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        label_data = data[0]
        assert label_data["device_color"] == "yellow"
        assert label_data["device_style"] == "lighten"
        assert label_data["label"] == "Important"
        assert label_data["highlight_count"] == 2
        assert label_data["label_source"] == "book"

    def test_get_book_labels_empty_book(self, client: TestClient, db_session: Session) -> None:
        """Test getting labels for a book with no highlight styles."""
        book = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Empty Labels Book",
            author="Test Author",
        )

        response = client.get(f"/api/v1/books/{book.id}/highlight-labels")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_get_book_labels_excludes_individual_level_styles(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that only combination-level styles (both color and style set) are returned."""
        book = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Individual Styles Book",
            author="Test Author",
        )

        # Create a combination-level style
        create_test_highlight_style(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            book_id=book.id,
            device_color="yellow",
            device_style="lighten",
            label="Combo",
        )

        # Create a color-only style (individual level)
        color_only = models.HighlightStyle(
            user_id=DEFAULT_USER_ID,
            book_id=book.id,
            device_color="green",
            device_style=None,
            label="Color Only",
        )
        db_session.add(color_only)
        db_session.commit()

        response = client.get(f"/api/v1/books/{book.id}/highlight-labels")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Only the combination-level style should be returned
        assert len(data) == 1
        assert data[0]["device_color"] == "yellow"
        assert data[0]["device_style"] == "lighten"


class TestUpdateHighlightLabel:
    """Test PATCH /api/v1/highlight-labels/{id} endpoint."""

    def test_update_label(self, client: TestClient, db_session: Session) -> None:
        """Test updating a highlight label."""
        book = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Update Label Book",
            author="Test Author",
        )

        style = create_test_highlight_style(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            book_id=book.id,
            device_color="yellow",
            device_style="lighten",
        )

        response = client.patch(
            f"/api/v1/highlight-labels/{style.id}",
            json={"label": "Very Important", "ui_color": "#ff0000"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["label"] == "Very Important"
        assert data["ui_color"] == "#ff0000"
        assert data["device_color"] == "yellow"
        assert data["device_style"] == "lighten"

    def test_update_label_not_found(self, client: TestClient) -> None:
        """Test updating a non-existent highlight label returns 404."""
        response = client.patch(
            "/api/v1/highlight-labels/99999",
            json={"label": "Does Not Exist"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetGlobalHighlightLabels:
    """Test GET /api/v1/highlight-labels/global endpoint."""

    def test_get_global_labels_empty(self, client: TestClient) -> None:
        """Test getting global labels when none exist."""
        response = client.get("/api/v1/highlight-labels/global")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_get_global_labels_returns_globals(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test getting global labels returns only global styles."""
        # Create a global style (book_id=None)
        global_style = models.HighlightStyle(
            user_id=DEFAULT_USER_ID,
            book_id=None,
            device_color="yellow",
            device_style=None,
            label="Yellow Global",
        )
        db_session.add(global_style)
        db_session.commit()

        # Create a book-scoped style (should NOT appear)
        book = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Scoped Book",
            author="Test Author",
        )
        create_test_highlight_style(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            book_id=book.id,
            device_color="green",
            device_style="lighten",
            label="Book Scoped",
        )

        response = client.get("/api/v1/highlight-labels/global")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        assert data[0]["device_color"] == "yellow"
        assert data[0]["label"] == "Yellow Global"
        assert data[0]["label_source"] == "global"


class TestCreateGlobalHighlightLabel:
    """Test POST /api/v1/highlight-labels/global endpoint."""

    def test_create_global_label(self, client: TestClient) -> None:
        """Test creating a global highlight label."""
        response = client.post(
            "/api/v1/highlight-labels/global",
            json={
                "device_color": "blue",
                "device_style": "lighten",
                "label": "Blue Highlights",
                "ui_color": "#0000ff",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["device_color"] == "blue"
        assert data["device_style"] == "lighten"
        assert data["label"] == "Blue Highlights"
        assert data["ui_color"] == "#0000ff"
        assert data["label_source"] == "global"
        assert data["highlight_count"] == 0
        assert "id" in data

    def test_create_global_label_color_only(self, client: TestClient) -> None:
        """Test creating a global label for just a color (no style)."""
        response = client.post(
            "/api/v1/highlight-labels/global",
            json={
                "device_color": "red",
                "device_style": None,
                "label": "Red Notes",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["device_color"] == "red"
        assert data["device_style"] is None
        assert data["label"] == "Red Notes"

    def test_create_global_label_appears_in_get(self, client: TestClient) -> None:
        """Test that a created global label appears in the GET endpoint."""
        # Create a global label
        create_response = client.post(
            "/api/v1/highlight-labels/global",
            json={
                "device_color": "purple",
                "device_style": "strikethrough",
                "label": "Disagreement",
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Verify it appears in the list
        get_response = client.get("/api/v1/highlight-labels/global")
        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()

        labels = [d["label"] for d in data]
        assert "Disagreement" in labels


class TestHighlightUploadWithLabels:
    """Test highlight upload integration with highlight labels."""

    def test_upload_creates_styles_and_labels_endpoint_works(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """End-to-end test: upload highlights, then query labels."""
        create_book_via_api(
            {
                "client_book_id": "test-e2e-labels",
                "title": "E2E Labels Book",
                "author": "Test Author",
            }
        )

        # Upload highlights with different styles
        payload = {
            "client_book_id": "test-e2e-labels",
            "highlights": [
                {
                    "text": "Yellow highlight 1",
                    "page": 10,
                    "datetime": "2024-01-15 14:00:00",
                    "color": "yellow",
                    "drawer": "lighten",
                },
                {
                    "text": "Yellow highlight 2",
                    "page": 20,
                    "datetime": "2024-01-15 15:00:00",
                    "color": "yellow",
                    "drawer": "lighten",
                },
                {
                    "text": "Green strikethrough",
                    "page": 30,
                    "datetime": "2024-01-15 16:00:00",
                    "color": "green",
                    "drawer": "strikethrough",
                },
            ],
        }
        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["highlights_created"] == 3

        # Get book ID
        book = db_session.query(models.Book).filter_by(title="E2E Labels Book").first()
        assert book is not None

        # Get labels for the book
        labels_response = client.get(f"/api/v1/books/{book.id}/highlight-labels")
        assert labels_response.status_code == status.HTTP_200_OK
        labels = labels_response.json()

        assert len(labels) == 2  # Two unique color+style combos

        # Find the yellow/lighten label
        yellow_labels = [lbl for lbl in labels if lbl["device_color"] == "yellow"]
        assert len(yellow_labels) == 1
        assert yellow_labels[0]["highlight_count"] == 2

        # Find the green/strikethrough label
        green_labels = [lbl for lbl in labels if lbl["device_color"] == "green"]
        assert len(green_labels) == 1
        assert green_labels[0]["highlight_count"] == 1

    def test_upload_without_color_drawer_still_creates_style(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that highlights without color/drawer still get a style (with None values)."""
        create_book_via_api(
            {
                "client_book_id": "test-no-color",
                "title": "No Color Book",
                "author": "Test Author",
            }
        )

        payload = {
            "client_book_id": "test-no-color",
            "highlights": [
                {
                    "text": "Plain highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:00:00",
                },
            ],
        }
        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK

        book = db_session.query(models.Book).filter_by(title="No Color Book").first()
        assert book is not None

        styles = db_session.query(models.HighlightStyle).filter_by(book_id=book.id).all()
        assert len(styles) == 1
        assert styles[0].device_color is None
        assert styles[0].device_style is None

        # The highlight should still reference the style
        highlight = db_session.query(models.Highlight).filter_by(book_id=book.id).first()
        assert highlight is not None
        assert highlight.highlight_style_id == styles[0].id
