"""Tests for EPUB text extraction using xpoints."""

from collections.abc import Generator
from pathlib import Path

import pytest
from ebooklib import epub
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.exceptions import XPointNavigationError, XPointParseError
from src.models import Book, User
from src.services.epub_service import EPUBS_DIR, EpubService
from tests.conftest import create_test_book


def create_test_epub(epub_path: Path, chapters: list[dict[str, str]]) -> None:
    """Create a test EPUB file with specified chapter content.

    Args:
        epub_path: Path where the EPUB will be saved
        chapters: List of dicts with 'title' and 'content' keys
    """
    book = epub.EpubBook()
    book.set_identifier("test-book-123")
    book.set_title("Test Book")
    book.set_language("en")
    book.add_author("Test Author")

    spine: list[str | epub.EpubHtml] = ["nav"]
    toc: list[epub.EpubHtml] = []

    for i, chapter_data in enumerate(chapters, 1):
        chapter = epub.EpubHtml(
            title=chapter_data["title"],
            file_name=f"chapter_{i}.xhtml",
            lang="en",
        )
        # Set content using set_content method for proper encoding
        chapter.set_content(
            f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{chapter_data["title"]}</title></head>
<body>
{chapter_data["content"]}
</body>
</html>""".encode()
        )
        book.add_item(chapter)
        spine.append(chapter)
        toc.append(chapter)

    book.toc = toc
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(epub_path), book)


@pytest.fixture
def test_epub_book(db_session: Session, test_user: User) -> Generator[Book, None, None]:
    """Create a test book with an EPUB file containing known content."""
    book = create_test_book(
        db_session=db_session,
        user_id=test_user.id,
        title="Test EPUB Book",
        author="Test Author",
    )

    # Update book with epub_path
    epub_filename = f"test_epub_{book.id}.epub"
    book.epub_path = epub_filename
    db_session.commit()

    # Create the epub file
    epub_path = EPUBS_DIR / epub_filename
    create_test_epub(
        epub_path,
        chapters=[
            {
                "title": "Chapter 1",
                "content": """<div>
<p>This is the first paragraph of chapter one.</p>
<p>This is the second paragraph with some important text.</p>
<p>And this is the third paragraph.</p>
</div>""",
            },
            {
                "title": "Chapter 2",
                "content": """<div>
<p>Chapter two begins here with new content.</p>
<p>More text in the second chapter.</p>
</div>""",
            },
        ],
    )

    yield book

    # Cleanup
    if epub_path.exists():
        epub_path.unlink()


class TestEpubTextExtraction:
    """Test suite for EPUB text extraction."""

    def test_extract_within_single_paragraph(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Extract text within a single paragraph."""
        service = EpubService(db_session)

        # Extract "the first paragraph" from first paragraph
        # DocFragment[2] = first chapter (spine[1], after nav)
        # The text "This is the first paragraph of chapter one." starts at position 0
        result = service.extract_text_between_xpoints(
            book_id=test_epub_book.id,
            user_id=test_user.id,
            start_xpoint="/body/DocFragment[2]/body/div/p[1]/text().8",  # "the"
            end_xpoint="/body/DocFragment[2]/body/div/p[1]/text().27",  # end of "first paragraph"
        )

        assert result == "the first paragraph"

    def test_extract_entire_paragraph(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Extract an entire paragraph's text."""
        service = EpubService(db_session)

        # DocFragment[2] = first chapter (spine[1], after nav)
        result = service.extract_text_between_xpoints(
            book_id=test_epub_book.id,
            user_id=test_user.id,
            start_xpoint="/body/DocFragment[2]/body/div/p[1]/text().0",
            end_xpoint="/body/DocFragment[2]/body/div/p[1]/text().44",
        )

        assert result == "This is the first paragraph of chapter one."

    def test_extract_with_doc_fragment(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Extract text using explicit DocFragment index."""
        service = EpubService(db_session)

        # DocFragment[2] is the first chapter (spine[0] is nav, spine[1] is chapter 1)
        result = service.extract_text_between_xpoints(
            book_id=test_epub_book.id,
            user_id=test_user.id,
            start_xpoint="/body/DocFragment[2]/body/div/p[1]/text().0",
            end_xpoint="/body/DocFragment[2]/body/div/p[1]/text().7",
        )

        assert result == "This is"

    def test_invalid_xpoint_raises_error(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Invalid xpoint format raises XPointParseError."""
        service = EpubService(db_session)

        with pytest.raises(XPointParseError):
            service.extract_text_between_xpoints(
                book_id=test_epub_book.id,
                user_id=test_user.id,
                start_xpoint="invalid",
                end_xpoint="/body/div/p[1]/text().10",
            )

    def test_xpath_not_found_raises_error(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """XPath that doesn't match any element raises XPointNavigationError."""
        service = EpubService(db_session)

        with pytest.raises(XPointNavigationError) as exc_info:
            service.extract_text_between_xpoints(
                book_id=test_epub_book.id,
                user_id=test_user.id,
                start_xpoint="/body/div/p[999]/text().0",
                end_xpoint="/body/div/p[999]/text().10",
            )

        assert "matched no elements" in str(exc_info.value)

    def test_doc_fragment_out_of_range(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """DocFragment index out of range raises XPointNavigationError."""
        service = EpubService(db_session)

        with pytest.raises(XPointNavigationError) as exc_info:
            service.extract_text_between_xpoints(
                book_id=test_epub_book.id,
                user_id=test_user.id,
                start_xpoint="/body/DocFragment[999]/body/div/p[1]/text().0",
                end_xpoint="/body/DocFragment[999]/body/div/p[1]/text().10",
            )

        assert "index out of range" in str(exc_info.value)

    def test_book_without_epub_raises_error(self, db_session: Session, test_user: User) -> None:
        """Book without epub_path raises HTTPException."""
        book = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Book Without EPUB",
        )

        service = EpubService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.extract_text_between_xpoints(
                book_id=book.id,
                user_id=test_user.id,
                start_xpoint="/body/div/p[1]/text().0",
                end_xpoint="/body/div/p[1]/text().10",
            )

        assert exc_info.value.status_code == 404
