"""Tests for xpoint parsing utility."""

import pytest

from src.exceptions import XPointParseError
from src.utils import ParsedXPoint, compare_xpoints, is_xpoint_in_range


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

    def test_parse_image_element_with_offset(self) -> None:
        """Parse image element with offset (no /text())."""
        result = ParsedXPoint.parse("/body/DocFragment[20]/body/div/p[1]/img.0")

        assert result.doc_fragment_index == 20
        assert result.xpath == "/body/div/p[1]/img"
        assert result.text_node_index == 1
        assert result.char_offset == 0

    def test_parse_element_with_offset_no_text(self) -> None:
        """Parse element with offset but no /text() specifier."""
        result = ParsedXPoint.parse("/body/span.5")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/span"
        assert result.text_node_index == 1
        assert result.char_offset == 5

    def test_parse_invalid_doc_fragment_index_zero(self) -> None:
        """DocFragment index < 1 raises error."""
        with pytest.raises(XPointParseError, match="DocFragment index must be >= 1"):
            ParsedXPoint.parse("/body/DocFragment[0]/body/div")

    def test_parse_invalid_text_node_index_zero(self) -> None:
        """Text node index < 1 raises error."""
        with pytest.raises(XPointParseError, match="text node index must be >= 1"):
            ParsedXPoint.parse("/body/div/text()[0].10")

    def test_parse_invalid_negative_offset(self) -> None:
        """Negative offset raises error."""
        with pytest.raises(XPointParseError):
            ParsedXPoint.parse("/body/div/text().-5")

    def test_parse_invalid_does_not_start_with_body(self) -> None:
        """XPoint not starting with /body raises error."""
        with pytest.raises(XPointParseError):
            ParsedXPoint.parse("/invalid/path")

    def test_parse_invalid_whitespace_in_path(self) -> None:
        """XPoint containing whitespace raises error."""
        with pytest.raises(XPointParseError):
            ParsedXPoint.parse("/body div")

    def test_parse_invalid_multiple_dots(self) -> None:
        """XPoint with multiple dots (malformed offset) raises error."""
        with pytest.raises(XPointParseError):
            ParsedXPoint.parse("/body/div.5.10")


class TestCompareXpoints:
    """Test suite for xpoint comparison functions."""

    def test_compare_identical_xpoints(self) -> None:
        """Identical xpoints should be equal."""
        xpoint = "/body/div[1]/p[5]/text()[1].42"
        assert compare_xpoints(xpoint, xpoint) == 0

    def test_compare_different_doc_fragments(self) -> None:
        """Earlier doc fragment comes first."""
        xpoint1 = "/body/DocFragment[1]/body/div/p/text().0"
        xpoint2 = "/body/DocFragment[2]/body/div/p/text().0"
        assert compare_xpoints(xpoint1, xpoint2) == -1
        assert compare_xpoints(xpoint2, xpoint1) == 1

    def test_compare_with_and_without_doc_fragment(self) -> None:
        """No DocFragment treated as DocFragment[1]."""
        xpoint1 = "/body/div/p/text().0"  # No DocFragment = 1
        xpoint2 = "/body/DocFragment[1]/body/div/p/text().0"  # Explicit DocFragment[1]
        assert compare_xpoints(xpoint1, xpoint2) == 0

    def test_compare_different_element_indices(self) -> None:
        """Earlier element index comes first."""
        xpoint1 = "/body/div[1]/p[5]/text().0"
        xpoint2 = "/body/div[1]/p[10]/text().0"
        assert compare_xpoints(xpoint1, xpoint2) == -1
        assert compare_xpoints(xpoint2, xpoint1) == 1

    def test_compare_avoids_lexicographic_trap(self) -> None:
        """Numeric comparison, not lexicographic (p[9] < p[10])."""
        xpoint1 = "/body/div/p[9]/text().0"
        xpoint2 = "/body/div/p[10]/text().0"
        # Lexicographically "p[9]" > "p[10]", but numerically p[9] < p[10]
        assert compare_xpoints(xpoint1, xpoint2) == -1

    def test_compare_different_text_node_indices(self) -> None:
        """Earlier text node index comes first."""
        xpoint1 = "/body/div/p/text()[1].0"
        xpoint2 = "/body/div/p/text()[2].0"
        assert compare_xpoints(xpoint1, xpoint2) == -1
        assert compare_xpoints(xpoint2, xpoint1) == 1

    def test_compare_different_char_offsets(self) -> None:
        """Earlier char offset comes first."""
        xpoint1 = "/body/div/p/text().10"
        xpoint2 = "/body/div/p/text().100"
        assert compare_xpoints(xpoint1, xpoint2) == -1
        assert compare_xpoints(xpoint2, xpoint1) == 1

    def test_compare_different_xpath_depth(self) -> None:
        """Shallower xpath comes first when prefix matches."""
        xpoint1 = "/body/div/p/text().0"
        xpoint2 = "/body/div/p/span/text().0"
        assert compare_xpoints(xpoint1, xpoint2) == -1
        assert compare_xpoints(xpoint2, xpoint1) == 1

    def test_compare_element_boundaries(self) -> None:
        """Element boundary xpoints compare correctly."""
        xpoint1 = "/body/DocFragment[14]/body/a"  # Offset 0 default
        xpoint2 = "/body/DocFragment[14]/body/a/text().10"
        assert compare_xpoints(xpoint1, xpoint2) == -1

    def test_compare_complex_xpoints(self) -> None:
        """Complex xpoints with multiple differing components."""
        xpoint1 = "/body/DocFragment[2]/body/div[1]/section[1]/p[5]/text()[1].42"
        xpoint2 = "/body/DocFragment[2]/body/div[1]/section[1]/p[5]/text()[1].100"
        assert compare_xpoints(xpoint1, xpoint2) == -1

        xpoint3 = "/body/DocFragment[2]/body/div[1]/section[2]/p[1]/text().0"
        assert compare_xpoints(xpoint1, xpoint3) == -1  # section[1] < section[2]


class TestIsXpointInRange:
    """Test suite for xpoint range checking."""

    def test_xpoint_within_range_inclusive(self) -> None:
        """Xpoint within range returns True (inclusive)."""
        start = "/body/div/p[1]/text().0"
        end = "/body/div/p[10]/text().100"
        xpoint = "/body/div/p[5]/text().50"
        assert is_xpoint_in_range(xpoint, start, end) is True

    def test_xpoint_at_start_inclusive(self) -> None:
        """Xpoint at start of range returns True (inclusive)."""
        start = "/body/div/p[1]/text().0"
        end = "/body/div/p[10]/text().100"
        assert is_xpoint_in_range(start, start, end) is True

    def test_xpoint_at_end_inclusive(self) -> None:
        """Xpoint at end of range returns True (inclusive)."""
        start = "/body/div/p[1]/text().0"
        end = "/body/div/p[10]/text().100"
        assert is_xpoint_in_range(end, start, end) is True

    def test_xpoint_before_range(self) -> None:
        """Xpoint before range returns False."""
        start = "/body/div/p[5]/text().0"
        end = "/body/div/p[10]/text().100"
        xpoint = "/body/div/p[1]/text().0"
        assert is_xpoint_in_range(xpoint, start, end) is False

    def test_xpoint_after_range(self) -> None:
        """Xpoint after range returns False."""
        start = "/body/div/p[1]/text().0"
        end = "/body/div/p[10]/text().100"
        xpoint = "/body/div/p[15]/text().0"
        assert is_xpoint_in_range(xpoint, start, end) is False

    def test_xpoint_at_start_exclusive(self) -> None:
        """Xpoint at start of range returns False (exclusive)."""
        start = "/body/div/p[1]/text().0"
        end = "/body/div/p[10]/text().100"
        assert is_xpoint_in_range(start, start, end, inclusive=False) is False

    def test_xpoint_at_end_exclusive(self) -> None:
        """Xpoint at end of range returns False (exclusive)."""
        start = "/body/div/p[1]/text().0"
        end = "/body/div/p[10]/text().100"
        assert is_xpoint_in_range(end, start, end, inclusive=False) is False

    def test_xpoint_within_range_exclusive(self) -> None:
        """Xpoint within range returns True (exclusive)."""
        start = "/body/div/p[1]/text().0"
        end = "/body/div/p[10]/text().100"
        xpoint = "/body/div/p[5]/text().50"
        assert is_xpoint_in_range(xpoint, start, end, inclusive=False) is True

    def test_range_with_doc_fragments(self) -> None:
        """Range check works with DocFragments."""
        start = "/body/DocFragment[2]/body/div/p[1]/text().0"
        end = "/body/DocFragment[5]/body/div/p[10]/text().100"
        xpoint_in = "/body/DocFragment[3]/body/div/p[5]/text().50"
        xpoint_out = "/body/DocFragment[1]/body/div/p[5]/text().50"
        assert is_xpoint_in_range(xpoint_in, start, end) is True
        assert is_xpoint_in_range(xpoint_out, start, end) is False
