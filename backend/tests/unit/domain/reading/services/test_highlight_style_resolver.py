"""Tests for HighlightStyleResolver domain service."""

from datetime import UTC, datetime

from src.domain.common.value_objects import BookId, HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.domain.reading.services.highlight_style_resolver import HighlightStyleResolver


def _make_style(
    id: int,
    book_id: int | None,
    color: str | None,
    style: str | None,
    label: str | None = None,
    ui_color: str | None = None,
) -> HighlightStyle:
    now = datetime.now(UTC)
    return HighlightStyle.create_with_id(
        id=HighlightStyleId(id),
        user_id=UserId(1),
        book_id=BookId(book_id) if book_id else None,
        device_color=color,
        device_style=style,
        label=label,
        ui_color=ui_color,
        created_at=now,
        updated_at=now,
    )


class TestHighlightStyleResolver:
    def test_resolve_combination_book_label(self) -> None:
        resolver = HighlightStyleResolver()
        style = _make_style(1, 10, "green", "lighten", label="Important")
        result = resolver.resolve(style, [style])
        assert result.label == "Important"
        assert result.source == "book"

    def test_resolve_color_only_book_fallback(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "green", "lighten")  # no label
        color_only = _make_style(2, 10, "green", None, label="Green Notes")
        result = resolver.resolve(combo, [combo, color_only])
        assert result.label == "Green Notes"
        assert result.source == "book"

    def test_resolve_style_only_book_fallback(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "green", "strikethrough")
        style_only = _make_style(2, 10, None, "strikethrough", label="Criticism")
        result = resolver.resolve(combo, [combo, style_only])
        assert result.label == "Criticism"
        assert result.source == "book"

    def test_resolve_global_combination_fallback(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "yellow", "lighten")
        global_combo = _make_style(2, None, "yellow", "lighten", label="Highlight")
        result = resolver.resolve(combo, [combo, global_combo])
        assert result.label == "Highlight"
        assert result.source == "global"

    def test_resolve_global_color_fallback(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "yellow", "lighten")
        global_color = _make_style(2, None, "yellow", None, label="Yellow")
        result = resolver.resolve(combo, [combo, global_color])
        assert result.label == "Yellow"
        assert result.source == "global"

    def test_resolve_global_style_fallback(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "yellow", "strikethrough")
        global_style = _make_style(2, None, None, "strikethrough", label="Struck")
        result = resolver.resolve(combo, [combo, global_style])
        assert result.label == "Struck"
        assert result.source == "global"

    def test_resolve_no_label(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "gray", "lighten")
        result = resolver.resolve(combo, [combo])
        assert result.label is None
        assert result.source == "none"

    def test_priority_book_over_global(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "green", "lighten")
        book_color = _make_style(2, 10, "green", None, label="Book Green")
        global_combo = _make_style(3, None, "green", "lighten", label="Global Combo")
        result = resolver.resolve(combo, [combo, book_color, global_combo])
        assert result.label == "Book Green"
        assert result.source == "book"

    def test_priority_combination_over_individual(self) -> None:
        resolver = HighlightStyleResolver()
        combo = _make_style(1, 10, "green", "lighten", label="Exact Match")
        book_color = _make_style(2, 10, "green", None, label="Color Only")
        result = resolver.resolve(combo, [combo, book_color])
        assert result.label == "Exact Match"
        assert result.source == "book"
