"""Tests for PositionIndex resolution."""

from src.domain.common.value_objects.position import Position
from src.domain.common.value_objects.position_index import PositionIndex


class TestPositionIndex:
    def test_resolve_simple_xpoint(self):
        index = PositionIndex({(1, "/body/div/p"): 5})
        pos = index.resolve("/body/DocFragment[1]/body/div/p")
        assert pos == Position(index=5, char_index=0)

    def test_resolve_with_char_offset(self):
        index = PositionIndex({(1, "/body/div/p"): 5})
        pos = index.resolve("/body/DocFragment[1]/body/div/p/text().42")
        assert pos == Position(index=5, char_index=42)

    def test_resolve_without_doc_fragment(self):
        index = PositionIndex({(1, "/body/div/p"): 5})
        pos = index.resolve("/body/div/p")
        assert pos == Position(index=5, char_index=0)

    def test_resolve_unknown_returns_none(self):
        index = PositionIndex({(1, "/body/div/p"): 5})
        pos = index.resolve("/body/DocFragment[2]/body/div/p")
        assert pos is None

    def test_resolve_invalid_xpoint_returns_none(self):
        index = PositionIndex({(1, "/body/div/p"): 5})
        pos = index.resolve("garbage")
        assert pos is None

    def test_ordering_across_fragments(self):
        index = PositionIndex({
            (1, "/body/p"): 3,
            (2, "/body/p"): 10,
        })
        pos1 = index.resolve("/body/DocFragment[1]/body/p")
        pos2 = index.resolve("/body/DocFragment[2]/body/p")
        assert pos1 is not None
        assert pos2 is not None
        assert pos1 < pos2
