"""Tests for EPUB text extraction using xpoints."""

from collections.abc import Generator
from pathlib import Path

import pytest
from ebooklib import epub
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from sqlalchemy.orm import Session

from src.application.library.services.ebook_text_extraction_service import (
    EbookTextExtractionService,
)
from src.application.library.use_cases.ebook_upload_use_case import EbookUploadUseCase
from src.config import EPUBS_DIR
from src.domain.common.value_objects import BookId, UserId
from src.exceptions import BookNotFoundError, XPointNavigationError, XPointParseError
from src.models import Book, User
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

    # Update book with file_path and file_type
    epub_filename = f"test_epub_{book.id}.epub"
    book.file_path = epub_filename
    book.file_type = "epub"
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
        service = EbookTextExtractionService(db_session)

        # Extract "the first paragraph" from first paragraph
        # DocFragment[2] = first chapter (spine[1], after nav)
        # The text "This is the first paragraph of chapter one." starts at position 0
        result = service.extract_text(
            book_id=BookId(test_epub_book.id),
            user_id=UserId(test_user.id),
            start="/body/DocFragment[2]/body/div/p[1]/text().8",  # "the"
            end="/body/DocFragment[2]/body/div/p[1]/text().27",  # end of "first paragraph"
        )

        assert result == "the first paragraph"

    def test_extract_entire_paragraph(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Extract an entire paragraph's text."""
        service = EbookTextExtractionService(db_session)

        # DocFragment[2] = first chapter (spine[1], after nav)
        result = service.extract_text(
            book_id=BookId(test_epub_book.id),
            user_id=UserId(test_user.id),
            start="/body/DocFragment[2]/body/div/p[1]/text().0",
            end="/body/DocFragment[2]/body/div/p[1]/text().44",
        )

        assert result == "This is the first paragraph of chapter one."

    def test_extract_with_doc_fragment(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Extract text using explicit DocFragment index."""
        service = EbookTextExtractionService(db_session)

        # DocFragment[2] is the first chapter (spine[0] is nav, spine[1] is chapter 1)
        result = service.extract_text(
            book_id=BookId(test_epub_book.id),
            user_id=UserId(test_user.id),
            start="/body/DocFragment[2]/body/div/p[1]/text().0",
            end="/body/DocFragment[2]/body/div/p[1]/text().7",
        )

        assert result == "This is"

    def test_invalid_xpoint_raises_error(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Invalid xpoint format raises XPointParseError."""
        service = EbookTextExtractionService(db_session)

        with pytest.raises(XPointParseError):
            service.extract_text(
                book_id=BookId(test_epub_book.id),
                user_id=UserId(test_user.id),
                start="invalid",
                end="/body/div/p[1]/text().10",
            )

    def test_xpath_not_found_raises_error(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """XPath that doesn't match any element raises XPointNavigationError."""
        service = EbookTextExtractionService(db_session)

        with pytest.raises(XPointNavigationError) as exc_info:
            service.extract_text(
                book_id=BookId(test_epub_book.id),
                user_id=UserId(test_user.id),
                start="/body/div/p[999]/text().0",
                end="/body/div/p[999]/text().10",
            )

        assert "matched no elements" in str(exc_info.value)

    def test_doc_fragment_out_of_range(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """DocFragment index out of range raises XPointNavigationError."""
        service = EbookTextExtractionService(db_session)

        with pytest.raises(XPointNavigationError) as exc_info:
            service.extract_text(
                book_id=BookId(test_epub_book.id),
                user_id=UserId(test_user.id),
                start="/body/DocFragment[999]/body/div/p[1]/text().0",
                end="/body/DocFragment[999]/body/div/p[1]/text().10",
            )

        assert "index out of range" in str(exc_info.value)

    def test_book_without_epub_raises_error(self, db_session: Session, test_user: User) -> None:
        """Book without file_path raises BookNotFoundError."""
        book = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Book Without EPUB",
        )

        service = EbookTextExtractionService(db_session)

        with pytest.raises(BookNotFoundError) as exc_info:
            service.extract_text(
                book_id=BookId(book.id),
                user_id=UserId(test_user.id),
                start="/body/div/p[1]/text().0",
                end="/body/div/p[1]/text().10",
            )

        assert exc_info.value.status_code == 404


class TestExtractChapterText:
    """Test suite for chapter-level text extraction by fragment range."""

    def test_single_fragment_chapter(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Extract text for a chapter spanning a single spine item."""
        service = EbookTextExtractionService(db_session)

        # DocFragment[2] = chapter 1, DocFragment[3] = chapter 2 (next chapter start)
        result = service.extract_chapter_text(
            book_id=BookId(test_epub_book.id),
            user_id=UserId(test_user.id),
            start_xpoint="/body/DocFragment[2]/body",
            end_xpoint="/body/DocFragment[3]/body",
        )

        assert "This is the first paragraph of chapter one." in result
        assert "second paragraph with some important text" in result
        assert "third paragraph" in result
        # Should NOT contain chapter 2 content
        assert "Chapter two begins here" not in result

    def test_last_chapter_no_end_xpoint(
        self, db_session: Session, test_epub_book: Book, test_user: User
    ) -> None:
        """Extract text for the last chapter (end_xpoint is None)."""
        service = EbookTextExtractionService(db_session)

        # DocFragment[3] = chapter 2, no end_xpoint = last chapter
        result = service.extract_chapter_text(
            book_id=BookId(test_epub_book.id),
            user_id=UserId(test_user.id),
            start_xpoint="/body/DocFragment[3]/body",
            end_xpoint=None,
        )

        assert "Chapter two begins here with new content." in result
        assert "More text in the second chapter." in result

    def test_multi_fragment_chapter(self, db_session: Session, test_user: User) -> None:
        """Extract text for a chapter spanning multiple spine items."""
        book = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Multi Fragment Book",
            author="Test Author",
        )
        epub_filename = f"test_multi_frag_{book.id}.epub"
        book.file_path = epub_filename
        book.file_type = "epub"
        db_session.commit()

        epub_path = EPUBS_DIR / epub_filename
        create_test_epub(
            epub_path,
            chapters=[
                {"title": "Part 1a", "content": "<p>First fragment of chapter.</p>"},
                {"title": "Part 1b", "content": "<p>Second fragment of chapter.</p>"},
                {"title": "Part 1c", "content": "<p>Third fragment of chapter.</p>"},
                {"title": "Chapter 2", "content": "<p>Next chapter starts here.</p>"},
            ],
        )

        try:
            service = EbookTextExtractionService(db_session)

            # Chapter spans fragments 2, 3, 4 (spine indices after nav)
            # Next chapter starts at fragment 5
            result = service.extract_chapter_text(
                book_id=BookId(book.id),
                user_id=UserId(test_user.id),
                start_xpoint="/body/DocFragment[2]/body",
                end_xpoint="/body/DocFragment[5]/body",
            )

            assert "First fragment of chapter." in result
            assert "Second fragment of chapter." in result
            assert "Third fragment of chapter." in result
            assert "Next chapter starts here." not in result
        finally:
            if epub_path.exists():
                epub_path.unlink()

    def test_same_fragment_chapters(self, db_session: Session, test_user: User) -> None:
        """Extract text when two chapters share the same spine item."""
        book = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Same Fragment Book",
            author="Test Author",
        )
        epub_filename = f"test_same_frag_{book.id}.epub"
        book.file_path = epub_filename
        book.file_type = "epub"
        db_session.commit()

        epub_path = EPUBS_DIR / epub_filename
        _create_shared_spine_epub(epub_path)

        try:
            service = EbookTextExtractionService(db_session)

            # Chapter 1 starts at section1, chapter 2 starts at section2 — same fragment
            result = service.extract_chapter_text(
                book_id=BookId(book.id),
                user_id=UserId(test_user.id),
                start_xpoint="/body/DocFragment[2]/body/section[1]",
                end_xpoint="/body/DocFragment[2]/body/section[2]",
            )

            assert "First chapter content in section one." in result
            assert "More text in chapter one." in result
            # Should NOT contain chapter 2 content
            assert "Second chapter content in section two." not in result
        finally:
            if epub_path.exists():
                epub_path.unlink()

    def test_same_fragment_fallback_body_level(self, db_session: Session, test_user: User) -> None:
        """Same fragment with both body-level XPoints returns full fragment text."""
        book = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Same Fragment Fallback Book",
            author="Test Author",
        )
        epub_filename = f"test_same_frag_fallback_{book.id}.epub"
        book.file_path = epub_filename
        book.file_type = "epub"
        db_session.commit()

        epub_path = EPUBS_DIR / epub_filename
        _create_shared_spine_epub(epub_path)

        try:
            service = EbookTextExtractionService(db_session)

            # Both XPoints at body level in same fragment — start_elem is end_elem
            # Returns all text from that body element (best effort)
            result = service.extract_chapter_text(
                book_id=BookId(book.id),
                user_id=UserId(test_user.id),
                start_xpoint="/body/DocFragment[2]/body",
                end_xpoint="/body/DocFragment[2]/body",
            )

            # Should return all text in the fragment (both sections)
            assert "First chapter content in section one." in result
            assert "Second chapter content in section two." in result
        finally:
            if epub_path.exists():
                epub_path.unlink()

    def test_precise_xpoint_cross_fragment(self, db_session: Session, test_user: User) -> None:
        """Extract text with precise XPoints spanning across fragments."""
        book = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Cross Fragment Precise Book",
            author="Test Author",
        )
        epub_filename = f"test_cross_frag_precise_{book.id}.epub"
        book.file_path = epub_filename
        book.file_type = "epub"
        db_session.commit()

        epub_path = EPUBS_DIR / epub_filename

        # Create EPUB: file 1 has two sections, file 2 has two sections
        epub_book = epub.EpubBook()
        epub_book.set_identifier("test-cross-precise")
        epub_book.set_title("Cross Fragment Precise")
        epub_book.set_language("en")

        ch1 = epub.EpubHtml(title="File 1", file_name="file_1.xhtml", lang="en")
        ch1.set_content(b"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>File 1</title></head>
<body>
<section id="sec1"><p>Chapter one text.</p></section>
<section id="sec2"><p>Chapter two starts here.</p></section>
</body>
</html>""")

        ch2 = epub.EpubHtml(title="File 2", file_name="file_2.xhtml", lang="en")
        ch2.set_content(b"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>File 2</title></head>
<body>
<section id="sec3"><p>Chapter two continues.</p></section>
<section id="sec4"><p>Chapter three text.</p></section>
</body>
</html>""")

        epub_book.add_item(ch1)
        epub_book.add_item(ch2)
        epub_book.toc = [ch1, ch2]
        epub_book.spine = ["nav", ch1, ch2]
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())

        epub_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(str(epub_path), epub_book)

        try:
            service = EbookTextExtractionService(db_session)

            # Chapter 2: starts at file_1 section[2], ends at file_2 section[2]
            result = service.extract_chapter_text(
                book_id=BookId(book.id),
                user_id=UserId(test_user.id),
                start_xpoint="/body/DocFragment[2]/body/section[2]",
                end_xpoint="/body/DocFragment[3]/body/section[2]",
            )

            assert "Chapter two starts here." in result
            assert "Chapter two continues." in result
            # Should NOT contain chapter 1 or chapter 3 content
            assert "Chapter one text." not in result
            assert "Chapter three text." not in result
        finally:
            if epub_path.exists():
                epub_path.unlink()

    def test_last_chapter_precise_xpoint(self, db_session: Session, test_user: User) -> None:
        """Extract last chapter with precise start XPoint (no end_xpoint)."""
        book = create_test_book(
            db_session=db_session,
            user_id=test_user.id,
            title="Last Chapter Precise Book",
            author="Test Author",
        )
        epub_filename = f"test_last_ch_precise_{book.id}.epub"
        book.file_path = epub_filename
        book.file_type = "epub"
        db_session.commit()

        epub_path = EPUBS_DIR / epub_filename
        _create_shared_spine_epub(epub_path)

        try:
            service = EbookTextExtractionService(db_session)

            # Last chapter starts at section[2] in fragment 2, no end
            result = service.extract_chapter_text(
                book_id=BookId(book.id),
                user_id=UserId(test_user.id),
                start_xpoint="/body/DocFragment[2]/body/section[2]",
                end_xpoint=None,
            )

            assert "Second chapter content in section two." in result
            # Should NOT contain section 1 content
            assert "First chapter content in section one." not in result
        finally:
            if epub_path.exists():
                epub_path.unlink()


def _create_shared_spine_epub(epub_path: Path) -> None:
    """Create an EPUB with multiple chapters sharing a single spine item.

    The EPUB has one content file with two sections (simulating chapters
    that share the same HTML file, distinguished by fragment IDs).
    """
    epub_book = epub.EpubBook()
    epub_book.set_identifier("test-shared-spine")
    epub_book.set_title("Shared Spine Test")
    epub_book.set_language("en")
    epub_book.add_author("Test Author")

    chapter = epub.EpubHtml(
        title="Shared File",
        file_name="shared.xhtml",
        lang="en",
    )
    chapter.set_content(b"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Shared File</title></head>
<body>
<section id="section1">
<p>First chapter content in section one.</p>
<p>More text in chapter one.</p>
</section>
<section id="section2">
<p>Second chapter content in section two.</p>
<p>More text in chapter two.</p>
</section>
</body>
</html>""")

    epub_book.add_item(chapter)
    epub_book.toc = [chapter]
    epub_book.spine = ["nav", chapter]
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())

    epub_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(epub_path), epub_book)


class TestResolveHrefToXpoint:
    """Test suite for _resolve_href_to_xpoint XPoint resolution."""

    def _make_epub_with_fragments(self, tmp_path: Path) -> epub.EpubBook:
        """Create an ebooklib EpubBook with known fragment IDs for testing.

        Writes and reads back the EPUB so spine items have proper
        (item_id, linear) tuple format as expected by _build_href_to_spine_index.
        """
        epub_book = epub.EpubBook()
        epub_book.set_identifier("test-resolve-xpoint")
        epub_book.set_title("Resolve XPoint Test")
        epub_book.set_language("en")

        ch1 = epub.EpubHtml(title="Chapter", file_name="chapter.xhtml", lang="en")
        ch1.set_content(b"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter</title></head>
<body>
<section id="intro"><p>Introduction text.</p></section>
<section id="main"><p>Main text.</p></section>
</body>
</html>""")

        epub_book.add_item(ch1)
        epub_book.spine = ["nav", ch1]
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())

        # Write and read back to get proper spine format
        epub_file = tmp_path / "test_resolve.epub"
        epub.write_epub(str(epub_file), epub_book)
        return epub.read_epub(str(epub_file))

    def test_href_with_fragment_resolves_to_precise_xpoint(self, tmp_path: Path) -> None:
        """Href with #fragment produces precise XPoint with element path."""
        epub_book = self._make_epub_with_fragments(tmp_path)
        spine_mapping = EbookUploadUseCase._build_href_to_spine_index(epub_book)  # pyright: ignore[reportPrivateUsage]
        html_cache: dict[int, etree._Element] = {}  # pyright: ignore[reportPrivateUsage]

        result = EbookUploadUseCase._resolve_href_to_xpoint(  # pyright: ignore[reportPrivateUsage]
            epub_book, "chapter.xhtml#main", spine_mapping, html_cache
        )

        assert result is not None
        assert "DocFragment[2]" in result
        assert "/body/section[2]" in result

    def test_href_without_fragment_returns_body_level(self, tmp_path: Path) -> None:
        """Href without #fragment produces body-level XPoint."""
        epub_book = self._make_epub_with_fragments(tmp_path)
        spine_mapping = EbookUploadUseCase._build_href_to_spine_index(epub_book)  # pyright: ignore[reportPrivateUsage]
        html_cache: dict[int, etree._Element] = {}  # pyright: ignore[reportPrivateUsage]

        result = EbookUploadUseCase._resolve_href_to_xpoint(  # pyright: ignore[reportPrivateUsage]
            epub_book, "chapter.xhtml", spine_mapping, html_cache
        )

        assert result == "/body/DocFragment[2]/body"

    def test_href_with_nonexistent_fragment_falls_back(self, tmp_path: Path) -> None:
        """Href with unknown #fragment falls back to body-level XPoint."""
        epub_book = self._make_epub_with_fragments(tmp_path)
        spine_mapping = EbookUploadUseCase._build_href_to_spine_index(epub_book)  # pyright: ignore[reportPrivateUsage]
        html_cache: dict[int, etree._Element] = {}  # pyright: ignore[reportPrivateUsage]

        result = EbookUploadUseCase._resolve_href_to_xpoint(  # pyright: ignore[reportPrivateUsage]
            epub_book, "chapter.xhtml#nonexistent", spine_mapping, html_cache
        )

        assert result == "/body/DocFragment[2]/body"

    def test_href_with_unknown_file_returns_none(self, tmp_path: Path) -> None:
        """Href pointing to unknown file returns None."""
        epub_book = self._make_epub_with_fragments(tmp_path)
        spine_mapping = EbookUploadUseCase._build_href_to_spine_index(epub_book)  # pyright: ignore[reportPrivateUsage]
        html_cache: dict[int, etree._Element] = {}  # pyright: ignore[reportPrivateUsage]

        result = EbookUploadUseCase._resolve_href_to_xpoint(  # pyright: ignore[reportPrivateUsage]
            epub_book, "unknown.xhtml#intro", spine_mapping, html_cache
        )

        assert result is None

    def test_html_cache_is_reused(self, tmp_path: Path) -> None:
        """Multiple calls for same spine item reuse cached HTML tree."""
        epub_book = self._make_epub_with_fragments(tmp_path)
        spine_mapping = EbookUploadUseCase._build_href_to_spine_index(epub_book)  # pyright: ignore[reportPrivateUsage]
        html_cache: dict[int, etree._Element] = {}  # pyright: ignore[reportPrivateUsage]

        EbookUploadUseCase._resolve_href_to_xpoint(  # pyright: ignore[reportPrivateUsage]
            epub_book, "chapter.xhtml#intro", spine_mapping, html_cache
        )
        assert 2 in html_cache
        cached_tree = html_cache[2]

        EbookUploadUseCase._resolve_href_to_xpoint(  # pyright: ignore[reportPrivateUsage]
            epub_book, "chapter.xhtml#main", spine_mapping, html_cache
        )
        # Same object in cache — not re-parsed
        assert html_cache[2] is cached_tree
