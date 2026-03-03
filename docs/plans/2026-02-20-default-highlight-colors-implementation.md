# Default Highlight UI Colors Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** When no explicit `ui_color` is set on a highlight style, the resolver returns a sensible default derived from the KOReader `device_color` name.

**Architecture:** Add a `KOREADER_DEFAULT_UI_COLORS` constant dict and a `_default_ui_color` helper to `HighlightStyleResolver`. After the existing priority chain resolves, if `ui_color` is still None, fill it from the map. No DB, entity, or API changes needed.

**Tech Stack:** Python, pytest, pyright

---

### Task 1: Add default color tests

**Files:**
- Modify: `backend/tests/unit/domain/reading/services/test_highlight_style_resolver.py`

**Step 1: Write failing tests**

Add these tests to the existing `TestHighlightStyleResolver` class:

```python
def test_default_ui_color_when_no_explicit_color(self) -> None:
    """When no ui_color is set anywhere, resolver returns default based on device_color."""
    resolver = HighlightStyleResolver()
    combo = _make_style(1, 10, "yellow", "lighten")
    result = resolver.resolve(combo, [combo])
    assert result.label is None
    assert result.ui_color == KOREADER_DEFAULT_UI_COLORS["yellow"]
    assert result.source == "none"

def test_explicit_ui_color_overrides_default(self) -> None:
    """When style has explicit ui_color, it takes precedence over the default."""
    resolver = HighlightStyleResolver()
    combo = _make_style(1, 10, "yellow", "lighten", ui_color="#CUSTOM1")
    result = resolver.resolve(combo, [combo])
    assert result.ui_color == "#CUSTOM1"

def test_default_ui_color_unknown_device_color(self) -> None:
    """Unknown device_color returns None for ui_color."""
    resolver = HighlightStyleResolver()
    combo = _make_style(1, 10, "magenta", "lighten")
    result = resolver.resolve(combo, [combo])
    assert result.ui_color is None

def test_default_ui_color_none_device_color(self) -> None:
    """None device_color returns None for ui_color."""
    resolver = HighlightStyleResolver()
    combo = _make_style(1, 10, None, "lighten")
    # Not combination-level, but test the fallback path
    result = resolver.resolve(combo, [combo])
    assert result.ui_color is None

def test_fallback_label_ui_color_uses_default_when_fallback_has_no_color(self) -> None:
    """When label comes from a fallback style that has no ui_color, default fills in."""
    resolver = HighlightStyleResolver()
    combo = _make_style(1, 10, "green", "lighten")  # no label, no ui_color
    color_only = _make_style(2, 10, "green", None, label="Green Notes")  # label but no ui_color
    result = resolver.resolve(combo, [combo, color_only])
    assert result.label == "Green Notes"
    assert result.ui_color == KOREADER_DEFAULT_UI_COLORS["green"]

def test_fallback_label_explicit_ui_color_preserved(self) -> None:
    """When label comes from a fallback style that has explicit ui_color, it's kept."""
    resolver = HighlightStyleResolver()
    combo = _make_style(1, 10, "green", "lighten")
    color_only = _make_style(2, 10, "green", None, label="Green Notes", ui_color="#00FF00")
    result = resolver.resolve(combo, [combo, color_only])
    assert result.label == "Green Notes"
    assert result.ui_color == "#00FF00"
```

Update the import at the top of the file:

```python
from src.domain.reading.services.highlight_style_resolver import (
    KOREADER_DEFAULT_UI_COLORS,
    HighlightStyleResolver,
)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/unit/domain/reading/services/test_highlight_style_resolver.py -v`

Expected: ImportError for `KOREADER_DEFAULT_UI_COLORS` and/or assertion failures on `ui_color`.

---

### Task 2: Implement default color fallback in resolver

**Files:**
- Modify: `backend/src/domain/reading/services/highlight_style_resolver.py`

**Step 1: Add the color map constant and apply fallback**

Add the constant dict at module level, before the class:

```python
KOREADER_DEFAULT_UI_COLORS: dict[str, str] = {
    "yellow": "#F59E0B",
    "green": "#10B981",
    "blue": "#3B82F6",
    "red": "#EF4444",
    "orange": "#F97316",
    "olive": "#84CC16",
    "cyan": "#06B6D4",
    "purple": "#8B5CF6",
    "gray": "#6B7280",
}
```

Add a private helper method to the class:

```python
def _apply_default_ui_color(
    self, resolved: ResolvedLabel, device_color: str | None
) -> ResolvedLabel:
    """Fill in default ui_color from device_color map when not explicitly set."""
    if resolved.ui_color is not None:
        return resolved
    default = KOREADER_DEFAULT_UI_COLORS.get(device_color or "")
    return ResolvedLabel(label=resolved.label, ui_color=default, source=resolved.source)
```

Modify `resolve()` to apply the fallback before every return. Change the three return sites:

1. Priority 1 return (line 38): wrap with `_apply_default_ui_color`
2. Priorities 2-6 return (line 62): wrap with `_apply_default_ui_color`
3. Priority 7 return (line 65): wrap with `_apply_default_ui_color`

The updated `resolve` method:

```python
def resolve(
    self,
    style: HighlightStyle,
    all_styles: list[HighlightStyle],
) -> ResolvedLabel:
    """Resolve effective label for a combination-level style."""
    # Priority 1: The style itself (combination + book)
    if style.label is not None:
        return self._apply_default_ui_color(
            ResolvedLabel(label=style.label, ui_color=style.ui_color, source="book"),
            style.device_color,
        )

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
            return self._apply_default_ui_color(resolved, style.device_color)

    # Priority 7: No label
    return self._apply_default_ui_color(
        ResolvedLabel(label=None, ui_color=style.ui_color, source="none"),
        style.device_color,
    )
```

**Step 2: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/unit/domain/reading/services/test_highlight_style_resolver.py -v`

Expected: All tests PASS (including the existing ones).

**Step 3: Run type checker**

Run: `cd backend && .venv/bin/pyright src/domain/reading/services/highlight_style_resolver.py`

Expected: No errors.

**Step 4: Run full test suite**

Run: `cd backend && .venv/bin/pytest`

Expected: All tests PASS.

**Step 5: Commit**

```bash
git add backend/src/domain/reading/services/highlight_style_resolver.py backend/tests/unit/domain/reading/services/test_highlight_style_resolver.py
git commit -m "feat: add default ui_color fallback from KOReader device colors"
```
