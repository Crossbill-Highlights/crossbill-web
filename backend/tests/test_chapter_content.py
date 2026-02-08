"""Tests for chapter content endpoint."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette import status

from src.models import Book, Chapter


def create_test_chapter(
    db_session: Session,
    book: Book,
    name: str,
    chapter_number: int,
    start_xpoint: str | None = None,
    end_xpoint: str | None = None,
    parent_id: int | None = None,
) -> Chapter:
    """Create a test chapter."""
    chapter = Chapter(
        book_id=book.id,
        name=name,
        chapter_number=chapter_number,
        start_xpoint=start_xpoint,
        end_xpoint=end_xpoint,
        parent_id=parent_id,
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter


class TestGetChapterContent:
    """Tests for GET /api/v1/chapters/{chapter_id}/content."""

    def test_get_chapter_content_success(
        self,
        client: TestClient,
        db_session: Session,
        test_book: Book,
    ) -> None:
        """Should return chapter text content from EPUB."""
        test_book.file_path = "test.epub"
        test_book.file_type = "epub"
        db_session.commit()

        chapter = create_test_chapter(
            db_session,
            test_book,
            name="Chapter 1: Introduction",
            chapter_number=1,
            start_xpoint="/body/DocFragment[1]/body/div[1]",
            end_xpoint="/body/DocFragment[1]/body/div[2]",
        )

        with (
            patch(
                "src.infrastructure.library.repositories.file_repository.FileRepository.find_epub"
            ) as mock_find_epub,
            patch(
                "src.infrastructure.library.services.epub_text_extraction_service."
                "EpubTextExtractionService.extract_chapter_text"
            ) as mock_extract,
        ):
            mock_find_epub.return_value = MagicMock(exists=lambda: True)
            mock_extract.return_value = "This is the chapter content."

            response = client.get(f"/api/v1/chapters/{chapter.id}/content")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["chapter_id"] == chapter.id
        assert data["chapter_name"] == "Chapter 1: Introduction"
        assert data["book_id"] == test_book.id
        assert data["content"] == "This is the chapter content."

    def test_get_chapter_content_not_found(
        self,
        client: TestClient,
    ) -> None:
        """Should return 404 for non-existent chapter."""
        response = client.get("/api/v1/chapters/99999/content")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_chapter_content_no_xpoint_data(
        self,
        client: TestClient,
        db_session: Session,
        test_book: Book,
    ) -> None:
        """Should return 400 when chapter has no position data."""
        chapter = create_test_chapter(
            db_session,
            test_book,
            name="Chapter Without XPoints",
            chapter_number=1,
            start_xpoint=None,
        )

        response = client.get(f"/api/v1/chapters/{chapter.id}/content")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "position data" in response.json()["detail"].lower()

    def test_get_chapter_content_no_epub(
        self,
        client: TestClient,
        db_session: Session,
        test_book: Book,
    ) -> None:
        """Should return 404 when book has no EPUB file."""
        chapter = create_test_chapter(
            db_session,
            test_book,
            name="Chapter 1",
            chapter_number=1,
            start_xpoint="/body/DocFragment[1]/body/div[1]",
        )

        response = client.get(f"/api/v1/chapters/{chapter.id}/content")
        assert response.status_code == status.HTTP_404_NOT_FOUND
