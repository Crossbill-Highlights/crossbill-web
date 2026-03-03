# Default Highlight UI Colors

## Problem

When KOReader uploads highlights, each highlight gets a `device_color` (e.g. "yellow", "green") and `device_style` (e.g. "lighten", "strikeout"). The `ui_color` field on `highlight_styles` is only populated when a user explicitly sets a custom color. When no custom color is set, the UI has no color to display.

KOReader has 9 predefined highlight colors. We should provide sensible default UI colors derived from these device color names.

## Design

### Approach: Resolver-level default fallback

The default color map lives in `HighlightStyleResolver`. When the resolved `ui_color` is None after walking the full priority chain, the resolver falls back to a default hex color based on `device_color`.

**Why this approach:**
- No database migration needed -- NULL `ui_color` means "use default"
- Single source of truth for the color map
- Easy to update when the UI color scheme changes (no data migration)
- `ui_color` in the DB becomes a pure user override

### Color Map

KOReader device colors mapped to UI hex values:

| device_color | ui_color (default) |
|---|---|
| yellow | #F59E0B |
| green | #10B981 |
| blue | #3B82F6 |
| red | #EF4444 |
| orange | #F97316 |
| olive | #84CC16 |
| cyan | #06B6D4 |
| purple | #8B5CF6 |
| gray | #6B7280 |

### Changes

**`backend/src/domain/reading/services/highlight_style_resolver.py`:**
- Add `KOREADER_DEFAULT_UI_COLORS` dict constant
- In `resolve()`, after the existing priority chain, if `ui_color` is None on the result, look up `style.device_color` in the map and return a new `ResolvedLabel` with the default color filled in

**No changes to:**
- `HighlightStyle` entity (no `create()` changes)
- Repository layer
- Database / migrations
- Router layer

### Tests

- Add test cases to `test_highlight_style_resolver.py` verifying:
  - Default color is returned when no `ui_color` set anywhere in chain
  - Explicit `ui_color` on style overrides the default
  - Unknown `device_color` returns None for `ui_color`
  - None `device_color` returns None for `ui_color`
