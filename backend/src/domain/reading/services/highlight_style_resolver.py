"""Domain service for resolving effective highlight labels via priority chain."""

from dataclasses import dataclass

from src.domain.reading.entities.highlight_style import HighlightStyle


@dataclass(frozen=True)
class ResolvedLabel:
    """Result of label resolution."""

    label: str | None
    ui_color: str | None
    source: str  # "book", "global", or "none"


class HighlightStyleResolver:
    """Resolves effective label and ui_color for a highlight style.

    Priority chain:
    1. Combination + book (book_id=X, color=Y, style=Z)
    2. Color-only + book (book_id=X, color=Y, style=NULL)
    3. Style-only + book (book_id=X, color=NULL, style=Z)
    4. Combination + global (book_id=NULL, color=Y, style=Z)
    5. Color-only + global (book_id=NULL, color=Y, style=NULL)
    6. Style-only + global (book_id=NULL, color=NULL, style=Z)
    7. No label
    """

    def resolve(
        self,
        style: HighlightStyle,
        all_styles: list[HighlightStyle],
    ) -> ResolvedLabel:
        """Resolve effective label for a combination-level style."""
        # Priority 1: The style itself (combination + book)
        if style.label is not None:
            return ResolvedLabel(label=style.label, ui_color=style.ui_color, source="book")

        book_styles = [s for s in all_styles if not s.is_global()]
        global_styles = [s for s in all_styles if s.is_global()]

        # Priorities 2-6: walk the fallback chain
        candidates: list[tuple[ResolvedLabel | None]] = [
            # Priority 2: Color-only + book
            (self._find_individual(book_styles, style.device_color, None, "book"),),
            # Priority 3: Style-only + book
            (self._find_individual(book_styles, None, style.device_style, "book"),),
            # Priority 4: Combination + global
            (
                self._find_combination(
                    global_styles, style.device_color, style.device_style, "global"
                ),
            ),
            # Priority 5: Color-only + global
            (self._find_individual(global_styles, style.device_color, None, "global"),),
            # Priority 6: Style-only + global
            (self._find_individual(global_styles, None, style.device_style, "global"),),
        ]
        for (resolved,) in candidates:
            if resolved:
                return resolved

        # Priority 7: No label
        return ResolvedLabel(label=None, ui_color=style.ui_color, source="none")

    def _find_combination(
        self,
        styles: list[HighlightStyle],
        color: str | None,
        style_name: str | None,
        source: str,
    ) -> ResolvedLabel | None:
        for s in styles:
            if (
                s.device_color == color
                and s.device_style == style_name
                and s.is_combination_level()
                and s.label is not None
            ):
                return ResolvedLabel(label=s.label, ui_color=s.ui_color or None, source=source)
        return None

    def _find_individual(
        self,
        styles: list[HighlightStyle],
        color: str | None,
        style_name: str | None,
        source: str,
    ) -> ResolvedLabel | None:
        for s in styles:
            if (
                color is not None
                and s.device_color == color
                and s.device_style is None
                and s.label is not None
            ):
                return ResolvedLabel(label=s.label, ui_color=s.ui_color or None, source=source)
            if (
                style_name is not None
                and s.device_style == style_name
                and s.device_color is None
                and s.label is not None
            ):
                return ResolvedLabel(label=s.label, ui_color=s.ui_color or None, source=source)
        return None
