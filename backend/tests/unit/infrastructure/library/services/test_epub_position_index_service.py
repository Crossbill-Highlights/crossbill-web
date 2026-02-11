"""Tests for EpubPositionIndexService."""

from pathlib import Path

import pytest
from ebooklib import epub

from src.domain.common.value_objects.position import Position
from src.infrastructure.library.services.epub_position_index_service import (
    EpubPositionIndexService,
)


def _create_test_epub(path: Path) -> Path:
    """Create a minimal EPUB for testing position index computation."""
    book = epub.EpubBook()
    book.set_identifier("test-book-123")
    book.set_title("Test Book")
    book.set_language("en")

    # Chapter 1: simple structure
    c1 = epub.EpubHtml(title="Chapter 1", file_name="chap01.xhtml", lang="en")
    c1.content = b"<html><body><h1>Chapter One</h1><p>First paragraph.</p><p>Second paragraph.</p></body></html>"
    book.add_item(c1)

    # Chapter 2: heterogeneous structure (the problematic case)
    c2 = epub.EpubHtml(title="Chapter 2", file_name="chap02.xhtml", lang="en")
    c2.content = b"<html><body><h2>Chapter Two</h2><p>Paragraph one.</p><blockquote>A quote.</blockquote><p>Paragraph two.</p></body></html>"
    book.add_item(c2)

    book.spine = [c1, c2]
    book.toc = [
        epub.Link("chap01.xhtml", "Chapter 1", "ch1"),
        epub.Link("chap02.xhtml", "Chapter 2", "ch2"),
    ]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub_path = path / "test.epub"
    epub.write_epub(str(epub_path), book)
    return epub_path


class TestEpubPositionIndexService:
    @pytest.fixture
    def epub_path(self, tmp_path: Path) -> Path:
        return _create_test_epub(tmp_path)

    @pytest.fixture
    def service(self) -> EpubPositionIndexService:
        return EpubPositionIndexService()

    def test_build_position_index_returns_index(self, service, epub_path):
        index = service.build_position_index(epub_path)
        assert index is not None

    def test_elements_in_first_spine_item_get_positions(self, service, epub_path):
        index = service.build_position_index(epub_path)
        body_pos = index.resolve("/body/DocFragment[1]/body")
        assert body_pos is not None
        assert body_pos.index >= 1

    def test_positions_increase_across_spine_items(self, service, epub_path):
        index = service.build_position_index(epub_path)
        chap1_pos = index.resolve("/body/DocFragment[1]/body")
        chap2_pos = index.resolve("/body/DocFragment[2]/body")
        assert chap1_pos is not None
        assert chap2_pos is not None
        assert chap1_pos < chap2_pos

    def test_sibling_elements_have_correct_order(self, service, epub_path):
        """This is THE critical test - heterogeneous siblings must be ordered correctly."""
        index = service.build_position_index(epub_path)
        # In chapter 2: h2, p[1], blockquote, p[2]
        h2_pos = index.resolve("/body/DocFragment[2]/body/h2")
        p1_pos = index.resolve("/body/DocFragment[2]/body/p")
        bq_pos = index.resolve("/body/DocFragment[2]/body/blockquote")
        p2_pos = index.resolve("/body/DocFragment[2]/body/p[2]")

        assert h2_pos is not None
        assert p1_pos is not None
        assert bq_pos is not None
        assert p2_pos is not None

        assert h2_pos < p1_pos < bq_pos < p2_pos

    def test_resolve_with_char_offset(self, service, epub_path):
        index = service.build_position_index(epub_path)
        pos = index.resolve("/body/DocFragment[1]/body/p/text().10")
        assert pos is not None
        assert pos.char_index == 10

    def test_resolve_unknown_xpoint_returns_none(self, service, epub_path):
        index = service.build_position_index(epub_path)
        pos = index.resolve("/body/DocFragment[99]/body/p")
        assert pos is None

    def test_resolve_invalid_xpoint_returns_none(self, service, epub_path):
        index = service.build_position_index(epub_path)
        pos = index.resolve("not a valid xpoint")
        assert pos is None
