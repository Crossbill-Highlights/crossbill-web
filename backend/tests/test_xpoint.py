"""Tests for xpoint parsing utility."""

import pytest

from src.exceptions import XPointParseError
from src.utils import ParsedXPoint


class TestParsedXPoint:
    """Test suite for ParsedXPoint parsing."""

    def test_parse_simple_xpoint(self) -> None:
        """Parse xpoint without DocFragment."""
        result = ParsedXPoint.parse("/body/div[1]/p[5]/text()[1].42")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div[1]/p[5]"
        assert result.text_node_index == 1
        assert result.char_offset == 42

    def test_parse_xpoint_with_doc_fragment(self) -> None:
        """Parse xpoint with DocFragment."""
        result = ParsedXPoint.parse("/body/DocFragment[12]/body/div/p[88]/text().223")

        assert result.doc_fragment_index == 12
        assert result.xpath == "/body/div/p[88]"
        assert result.text_node_index == 1  # Default when not specified
        assert result.char_offset == 223

    def test_parse_xpoint_with_explicit_text_node_index(self) -> None:
        """Parse xpoint with explicit text node index."""
        result = ParsedXPoint.parse("/body/div/p/text()[3].100")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div/p"
        assert result.text_node_index == 3
        assert result.char_offset == 100

    def test_parse_xpoint_zero_offset(self) -> None:
        """Parse xpoint with zero character offset."""
        result = ParsedXPoint.parse("/body/div/p/text().0")

        assert result.char_offset == 0

    def test_parse_xpoint_complex_xpath(self) -> None:
        """Parse xpoint with complex nested xpath."""
        result = ParsedXPoint.parse(
            "/body/DocFragment[1]/body/div[2]/section[1]/article/p[15]/text()[2].50"
        )

        assert result.doc_fragment_index == 1
        assert result.xpath == "/body/div[2]/section[1]/article/p[15]"
        assert result.text_node_index == 2
        assert result.char_offset == 50

    def test_parse_element_boundary_without_text(self) -> None:
        """Parse xpoint pointing to element boundary (no /text().offset)."""
        result = ParsedXPoint.parse("/body/DocFragment[14]/body/a")

        assert result.doc_fragment_index == 14
        assert result.xpath == "/body/a"
        assert result.text_node_index == 1  # Default
        assert result.char_offset == 0  # Default

    def test_parse_element_boundary_simple(self) -> None:
        """Parse simple element boundary xpoint."""
        result = ParsedXPoint.parse("/body/div/p")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div/p"
        assert result.text_node_index == 1
        assert result.char_offset == 0

    def test_parse_element_boundary_with_index(self) -> None:
        """Parse element boundary with indexed element."""
        result = ParsedXPoint.parse("/body/div[3]/span[2]")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div[3]/span[2]"
        assert result.text_node_index == 1
        assert result.char_offset == 0

    def test_parse_invalid_xpoint_missing_text(self) -> None:
        """Invalid xpoint missing text() raises error."""
        with pytest.raises(XPointParseError) as exc_info:
            ParsedXPoint.parse("/body/div/p.42")

        assert "does not match expected xpoint format" in str(exc_info.value)

    def test_parse_invalid_xpoint_missing_offset(self) -> None:
        """Invalid xpoint missing offset raises error."""
        with pytest.raises(XPointParseError) as exc_info:
            ParsedXPoint.parse("/body/div/p/text()")

        assert "does not match expected xpoint format" in str(exc_info.value)

    def test_parse_invalid_xpoint_empty_string(self) -> None:
        """Empty string raises error."""
        with pytest.raises(XPointParseError) as exc_info:
            ParsedXPoint.parse("")

        assert "does not match expected xpoint format" in str(exc_info.value)

    def test_parse_invalid_xpoint_random_string(self) -> None:
        """Random string raises error."""
        with pytest.raises(XPointParseError) as exc_info:
            ParsedXPoint.parse("not an xpoint")

        assert "does not match expected xpoint format" in str(exc_info.value)

    def test_parse_preserves_xpoint_in_error(self) -> None:
        """XPointParseError includes the invalid xpoint."""
        invalid_xpoint = "invalid/xpoint/format"
        with pytest.raises(XPointParseError) as exc_info:
            ParsedXPoint.parse(invalid_xpoint)

        assert exc_info.value.xpoint == invalid_xpoint

    def test_parsed_xpoint_is_frozen(self) -> None:
        """ParsedXPoint instances are immutable."""
        result = ParsedXPoint.parse("/body/div/p/text().10")

        with pytest.raises(AttributeError):
            result.char_offset = 20  # type: ignore[misc]
