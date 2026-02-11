"""Tests for XPoint value objects."""

import pytest

from src.domain.common.value_objects.xpoint import XPoint, XPointRange
from src.exceptions import XPointParseError


class TestXPoint:
    """Test suite for XPoint parsing and operations."""

    def test_parse_simple_xpoint(self) -> None:
        """Parse xpoint without DocFragment."""
        result = XPoint.parse("/body/div[1]/p[5]/text()[1].42")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div[1]/p[5]"
        assert result.text_node_index == 1
        assert result.char_offset == 42

    def test_parse_xpoint_with_doc_fragment(self) -> None:
        """Parse xpoint with DocFragment."""
        result = XPoint.parse("/body/DocFragment[12]/body/div/p[88]/text().223")

        assert result.doc_fragment_index == 12
        assert result.xpath == "/body/div/p[88]"
        assert result.text_node_index == 1  # Default when not specified
        assert result.char_offset == 223

    def test_parse_xpoint_with_explicit_text_node_index(self) -> None:
        """Parse xpoint with explicit text node index."""
        result = XPoint.parse("/body/div/p/text()[3].100")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div/p"
        assert result.text_node_index == 3
        assert result.char_offset == 100

    def test_parse_xpoint_zero_offset(self) -> None:
        """Parse xpoint with zero character offset."""
        result = XPoint.parse("/body/div/p/text().0")

        assert result.char_offset == 0

    def test_parse_xpoint_complex_xpath(self) -> None:
        """Parse xpoint with complex nested xpath."""
        result = XPoint.parse(
            "/body/DocFragment[1]/body/div[2]/section[1]/article/p[15]/text()[2].50"
        )

        assert result.doc_fragment_index == 1
        assert result.xpath == "/body/div[2]/section[1]/article/p[15]"
        assert result.text_node_index == 2
        assert result.char_offset == 50

    def test_parse_element_boundary_without_text(self) -> None:
        """Parse xpoint pointing to element boundary (no /text().offset)."""
        result = XPoint.parse("/body/DocFragment[14]/body/a")

        assert result.doc_fragment_index == 14
        assert result.xpath == "/body/a"
        assert result.text_node_index == 1  # Default
        assert result.char_offset == 0  # Default

    def test_parse_element_boundary_simple(self) -> None:
        """Parse simple element boundary xpoint."""
        result = XPoint.parse("/body/div/p")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div/p"
        assert result.text_node_index == 1
        assert result.char_offset == 0

    def test_parse_element_boundary_with_index(self) -> None:
        """Parse element boundary with indexed element."""
        result = XPoint.parse("/body/div[3]/span[2]")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/div[3]/span[2]"
        assert result.text_node_index == 1
        assert result.char_offset == 0

    def test_parse_invalid_xpoint_missing_offset(self) -> None:
        """Invalid xpoint missing offset raises error."""
        with pytest.raises(XPointParseError) as exc_info:
            XPoint.parse("/body/div/p/text()")

        assert "does not match expected xpoint format" in str(exc_info.value)

    def test_parse_invalid_xpoint_empty_string(self) -> None:
        """Empty string raises error."""
        with pytest.raises(XPointParseError) as exc_info:
            XPoint.parse("")

        assert "does not match expected xpoint format" in str(exc_info.value)

    def test_parse_invalid_xpoint_random_string(self) -> None:
        """Random string raises error."""
        with pytest.raises(XPointParseError) as exc_info:
            XPoint.parse("not an xpoint")

        assert "does not match expected xpoint format" in str(exc_info.value)

    def test_parse_preserves_xpoint_in_error(self) -> None:
        """XPointParseError includes the invalid xpoint."""
        invalid_xpoint = "invalid/xpoint/format"
        with pytest.raises(XPointParseError) as exc_info:
            XPoint.parse(invalid_xpoint)

        assert exc_info.value.xpoint == invalid_xpoint

    def test_parsed_xpoint_is_frozen(self) -> None:
        """XPoint instances are immutable."""
        result = XPoint.parse("/body/div/p/text().10")

        with pytest.raises(AttributeError):
            result.char_offset = 20  # type: ignore[misc]

    def test_parse_image_element_with_offset(self) -> None:
        """Parse image element with offset (no /text())."""
        result = XPoint.parse("/body/DocFragment[20]/body/div/p[1]/img.0")

        assert result.doc_fragment_index == 20
        assert result.xpath == "/body/div/p[1]/img"
        assert result.text_node_index == 1
        assert result.char_offset == 0

    def test_parse_element_with_offset_no_text(self) -> None:
        """Parse element with offset but no /text() specifier."""
        result = XPoint.parse("/body/span.5")

        assert result.doc_fragment_index is None
        assert result.xpath == "/body/span"
        assert result.text_node_index == 1
        assert result.char_offset == 5

    def test_parse_invalid_doc_fragment_index_zero(self) -> None:
        """DocFragment index < 1 raises error."""
        with pytest.raises(XPointParseError, match="DocFragment index must be >= 1"):
            XPoint.parse("/body/DocFragment[0]/body/div")

    def test_parse_invalid_text_node_index_zero(self) -> None:
        """Text node index < 1 raises error."""
        with pytest.raises(XPointParseError, match="text node index must be >= 1"):
            XPoint.parse("/body/div/text()[0].10")

    def test_parse_invalid_negative_offset(self) -> None:
        """Negative offset raises error."""
        with pytest.raises(XPointParseError):
            XPoint.parse("/body/div/text().-5")

    def test_parse_invalid_does_not_start_with_body(self) -> None:
        """XPoint not starting with /body raises error."""
        with pytest.raises(XPointParseError):
            XPoint.parse("/invalid/path")

    def test_parse_invalid_whitespace_in_path(self) -> None:
        """XPoint containing whitespace raises error."""
        with pytest.raises(XPointParseError):
            XPoint.parse("/body div")

    def test_parse_invalid_multiple_dots(self) -> None:
        """XPoint with multiple dots (malformed offset) raises error."""
        with pytest.raises(XPointParseError):
            XPoint.parse("/body/div.5.10")

    def test_to_string_simple_xpoint(self) -> None:
        """Convert XPoint back to string."""
        xpoint = XPoint.parse("/body/div[1]/p[5]/text()[1].42")
        assert xpoint.to_string() == "/body/div[1]/p[5]/text().42"

    def test_to_string_with_doc_fragment(self) -> None:
        """Convert XPoint with DocFragment to string."""
        xpoint = XPoint.parse("/body/DocFragment[12]/body/div/p[88]/text().223")
        assert xpoint.to_string() == "/body/DocFragment[12]/body/div/p[88]/text().223"

    def test_to_string_element_boundary(self) -> None:
        """Convert element boundary XPoint to string."""
        xpoint = XPoint.parse("/body/div/p")
        assert xpoint.to_string() == "/body/div/p"

    def test_to_dict_and_from_dict(self) -> None:
        """XPoint can be serialized to dict and back."""
        original = XPoint.parse("/body/DocFragment[12]/body/div/p[88]/text()[2].223")
        xpoint_dict = original.to_dict()
        restored = XPoint.from_dict(xpoint_dict)

        assert restored == original
        assert restored.doc_fragment_index == 12
        assert restored.xpath == "/body/div/p[88]"
        assert restored.text_node_index == 2
        assert restored.char_offset == 223


class TestXPointComparison:
    """Test suite for XPoint comparison operations."""

    def test_compare_identical_xpoints(self) -> None:
        """Identical xpoints should be equal."""
        xpoint1 = XPoint.parse("/body/div[1]/p[5]/text()[1].42")
        xpoint2 = XPoint.parse("/body/div[1]/p[5]/text()[1].42")
        assert xpoint1.compare_to(xpoint2) == 0

    def test_compare_different_doc_fragments(self) -> None:
        """Earlier doc fragment comes first."""
        xpoint1 = XPoint.parse("/body/DocFragment[1]/body/div/p/text().0")
        xpoint2 = XPoint.parse("/body/DocFragment[2]/body/div/p/text().0")
        assert xpoint1.compare_to(xpoint2) == -1
        assert xpoint2.compare_to(xpoint1) == 1

    def test_compare_with_and_without_doc_fragment(self) -> None:
        """No DocFragment treated as DocFragment[1]."""
        xpoint1 = XPoint.parse("/body/div/p/text().0")  # No DocFragment = 1
        xpoint2 = XPoint.parse(
            "/body/DocFragment[1]/body/div/p/text().0"
        )  # Explicit DocFragment[1]
        assert xpoint1.compare_to(xpoint2) == 0

    def test_compare_different_element_indices(self) -> None:
        """Earlier element index comes first."""
        xpoint1 = XPoint.parse("/body/div[1]/p[5]/text().0")
        xpoint2 = XPoint.parse("/body/div[1]/p[10]/text().0")
        assert xpoint1.compare_to(xpoint2) == -1
        assert xpoint2.compare_to(xpoint1) == 1

    def test_compare_avoids_lexicographic_trap(self) -> None:
        """Numeric comparison, not lexicographic (p[9] < p[10])."""
        xpoint1 = XPoint.parse("/body/div/p[9]/text().0")
        xpoint2 = XPoint.parse("/body/div/p[10]/text().0")
        # Lexicographically "p[9]" > "p[10]", but numerically p[9] < p[10]
        assert xpoint1.compare_to(xpoint2) == -1

    def test_compare_different_text_node_indices(self) -> None:
        """Earlier text node index comes first."""
        xpoint1 = XPoint.parse("/body/div/p/text()[1].0")
        xpoint2 = XPoint.parse("/body/div/p/text()[2].0")
        assert xpoint1.compare_to(xpoint2) == -1
        assert xpoint2.compare_to(xpoint1) == 1

    def test_compare_different_char_offsets(self) -> None:
        """Earlier char offset comes first."""
        xpoint1 = XPoint.parse("/body/div/p/text().10")
        xpoint2 = XPoint.parse("/body/div/p/text().100")
        assert xpoint1.compare_to(xpoint2) == -1
        assert xpoint2.compare_to(xpoint1) == 1

    def test_compare_different_xpath_depth(self) -> None:
        """Shallower xpath comes first when prefix matches."""
        xpoint1 = XPoint.parse("/body/div/p/text().0")
        xpoint2 = XPoint.parse("/body/div/p/span/text().0")
        assert xpoint1.compare_to(xpoint2) == -1
        assert xpoint2.compare_to(xpoint1) == 1

    def test_compare_element_boundaries(self) -> None:
        """Element boundary xpoints compare correctly."""
        xpoint1 = XPoint.parse("/body/DocFragment[14]/body/a")  # Offset 0 default
        xpoint2 = XPoint.parse("/body/DocFragment[14]/body/a/text().10")
        assert xpoint1.compare_to(xpoint2) == -1

    def test_compare_complex_xpoints(self) -> None:
        """Complex xpoints with multiple differing components."""
        xpoint1 = XPoint.parse("/body/DocFragment[2]/body/div[1]/section[1]/p[5]/text()[1].42")
        xpoint2 = XPoint.parse("/body/DocFragment[2]/body/div[1]/section[1]/p[5]/text()[1].100")
        assert xpoint1.compare_to(xpoint2) == -1

        xpoint3 = XPoint.parse("/body/DocFragment[2]/body/div[1]/section[2]/p[1]/text().0")
        assert xpoint1.compare_to(xpoint3) == -1  # section[1] < section[2]

    def test_compare_different_element_names_returns_none(self) -> None:
        """Different element names at the same depth are incomparable."""
        xpoint1 = XPoint.parse("/body/div[1]/p[5]/text().0")
        xpoint2 = XPoint.parse("/body/div[1]/table[1]/text().0")
        assert xpoint1.compare_to(xpoint2) is None
        assert xpoint2.compare_to(xpoint1) is None

    def test_compare_different_names_deeper_in_path(self) -> None:
        """Different element names deeper in the xpath are also incomparable."""
        xpoint1 = XPoint.parse("/body/DocFragment[14]/body/div[1]/section[2]/p[1]/text().0")
        xpoint2 = XPoint.parse(
            "/body/DocFragment[14]/body/div[1]/section[2]/blockquote[1]/text().0"
        )
        assert xpoint1.compare_to(xpoint2) is None

    def test_compare_same_fragment_different_body_children(self) -> None:
        """Different element names as body children are incomparable."""
        xpoint1 = XPoint.parse("/body/DocFragment[14]/body/h2/text().0")
        xpoint2 = XPoint.parse("/body/DocFragment[14]/body/div[1]/text().0")
        assert xpoint1.compare_to(xpoint2) is None


class TestXPointRange:
    """Test suite for XPointRange operations."""

    def test_xpoint_within_range_inclusive(self) -> None:
        """XPoint within range returns True (inclusive)."""
        xpoint_range = XPointRange.parse("/body/div/p[1]/text().0", "/body/div/p[10]/text().100")
        xpoint = XPoint.parse("/body/div/p[5]/text().50")
        assert xpoint_range.contains(xpoint) is True

    def test_xpoint_at_start_inclusive(self) -> None:
        """XPoint at start of range returns True (inclusive)."""
        xpoint_range = XPointRange.parse("/body/div/p[1]/text().0", "/body/div/p[10]/text().100")
        start = XPoint.parse("/body/div/p[1]/text().0")
        assert xpoint_range.contains(start) is True

    def test_xpoint_at_end_inclusive(self) -> None:
        """XPoint at end of range returns True (inclusive)."""
        xpoint_range = XPointRange.parse("/body/div/p[1]/text().0", "/body/div/p[10]/text().100")
        end = XPoint.parse("/body/div/p[10]/text().100")
        assert xpoint_range.contains(end) is True

    def test_xpoint_before_range(self) -> None:
        """XPoint before range returns False."""
        xpoint_range = XPointRange.parse("/body/div/p[5]/text().0", "/body/div/p[10]/text().100")
        xpoint = XPoint.parse("/body/div/p[1]/text().0")
        assert xpoint_range.contains(xpoint) is False

    def test_xpoint_after_range(self) -> None:
        """XPoint after range returns False."""
        xpoint_range = XPointRange.parse("/body/div/p[1]/text().0", "/body/div/p[10]/text().100")
        xpoint = XPoint.parse("/body/div/p[15]/text().0")
        assert xpoint_range.contains(xpoint) is False

    def test_range_with_doc_fragments(self) -> None:
        """Range check works with DocFragments."""
        xpoint_range = XPointRange.parse(
            "/body/DocFragment[2]/body/div/p[1]/text().0",
            "/body/DocFragment[5]/body/div/p[10]/text().100",
        )
        xpoint_in = XPoint.parse("/body/DocFragment[3]/body/div/p[5]/text().50")
        xpoint_out = XPoint.parse("/body/DocFragment[1]/body/div/p[5]/text().50")
        assert xpoint_range.contains(xpoint_in) is True
        assert xpoint_range.contains(xpoint_out) is False

    def test_contains_returns_false_when_comparison_inconclusive(self) -> None:
        """Contains returns False when element names differ at the divergence point.

        This prevents false positives where a highlight from a completely different
        part of the book matches because its element name happens to fall alphabetically
        between the range's start and end element names.
        """
        # Session range: starts at p[15], ends at table[1] (different element names)
        xpoint_range = XPointRange(
            start=XPoint.parse("/body/DocFragment[14]/body/div[1]/p[15]/text().0"),
            end=XPoint.parse("/body/DocFragment[14]/body/div[1]/table[1]/text().50"),
        )
        # Highlight in a "section" element - alphabetically between "p" and "table"
        # but could be anywhere in the actual document
        highlight = XPoint.parse("/body/DocFragment[14]/body/div[1]/section[1]/p[3]/text().100")
        assert xpoint_range.contains(highlight) is False

    def test_contains_works_when_elements_match(self) -> None:
        """Contains works normally when all element names match at each level."""
        xpoint_range = XPointRange.parse(
            "/body/DocFragment[14]/body/div[1]/p[15]/text().0",
            "/body/DocFragment[14]/body/div[1]/p[20]/text().100",
        )
        highlight_in = XPoint.parse("/body/DocFragment[14]/body/div[1]/p[17]/text().50")
        highlight_out = XPoint.parse("/body/DocFragment[14]/body/div[1]/p[5]/text().50")
        assert xpoint_range.contains(highlight_in) is True
        assert xpoint_range.contains(highlight_out) is False

    def test_xpoint_range_validation_invalid_order(self) -> None:
        """XPointRange validates that start comes before end."""
        with pytest.raises(ValueError, match="Start XPoint must come before end XPoint"):
            XPointRange.parse(
                "/body/DocFragment[5]/body/div/p[1]/text().0",
                "/body/DocFragment[2]/body/div/p[1]/text().0",
            )

    def test_xpoint_range_validation_same_element_invalid_offset(self) -> None:
        """XPointRange validates offsets in same element."""
        with pytest.raises(ValueError, match="Start offset must be <= end offset"):
            XPointRange.parse("/body/div/p/text().100", "/body/div/p/text().50")

    def test_xpoint_range_validation_invalid_text_node(self) -> None:
        """XPointRange validates text node indices."""
        with pytest.raises(ValueError, match="Start text node must be <= end text node"):
            XPointRange.parse("/body/div/p/text()[3].0", "/body/div/p/text()[1].0")

    def test_xpoint_range_to_dict_and_from_dict(self) -> None:
        """XPointRange can be serialized to dict and back."""
        original = XPointRange.parse(
            "/body/DocFragment[2]/body/div/p[1]/text().0",
            "/body/DocFragment[5]/body/div/p[10]/text().100",
        )
        range_dict = original.to_dict()
        restored = XPointRange.from_dict(range_dict)

        assert restored.start == original.start
        assert restored.end == original.end
