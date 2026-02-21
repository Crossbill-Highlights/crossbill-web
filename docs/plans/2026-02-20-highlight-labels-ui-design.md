# Highlight Labels UI Design

## Overview

Add frontend UI for the highlight labels feature. The backend already provides resolved labels (text + ui_color) per highlight and a dedicated highlight-labels API for listing and editing labels. This design covers displaying labels, editing them, and filtering highlights by label.

## Data Flow

### Display (inline)

Each `Highlight` in the `BookDetails` response already includes `label: { highlight_style_id, text, ui_color }`. No new API calls needed for display.

### Sidebar label list

Uses `GET /books/{book_id}/highlight-labels` via `useGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGet`. Returns `HighlightLabelInBook[]` with `id`, `device_color`, `device_style`, `label`, `ui_color`, `label_source`, `highlight_count`.

### Label editing

Uses `PATCH /highlight-labels/{style_id}` via `useUpdateHighlightLabelApiV1HighlightLabelsStyleIdPatch`. Sends `{ label?, ui_color? }`. After mutation, invalidates both book details and highlight-labels queries.

### Label filtering

New `labelId` URL search param. Filtering checks `highlight.label?.highlight_style_id === selectedLabelId`.

## Components

### LabelIndicator

**File:** `frontend/src/pages/BookPage/common/LabelIndicator.tsx`

Shared display component for the colored dot or chip.

- **Props:** `label: HighlightLabel | null | undefined`, `onClick?: () => void`, `size?: 'small' | 'medium'`
- If `label` is null/undefined or has no `ui_color`: renders nothing
- If `label.text` is set: renders MUI `Chip` with `backgroundColor` from `ui_color`, appropriate text contrast color, and label text
- If `label.text` is not set: renders a small colored circle (Box with `borderRadius: '50%'` and `backgroundColor: ui_color`)
- `size='small'` for HighlightCard, `size='medium'` for HighlightViewModal
- When `onClick` is provided: pointer cursor and subtle hover effect

### LabelEditorPopover

**File:** `frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/components/LabelEditorPopover.tsx`

Popover for editing label text and color, anchored to the clicked dot/chip.

- **Props:** `anchorEl`, `open`, `onClose`, `styleId: number`, `currentLabel?: string`, `currentColor?: string`, `bookId: number`
- Contains a `TextField` for label name (auto-focus, submit on Enter/blur)
- Contains a `CirclePicker` from `react-color` with ~12-16 predefined colors (including KOReader defaults: yellow #F59E0B, green #10B981, blue #3B82F6, red #EF4444, orange #F97316, olive #84CC16, cyan #06B6D4, purple #8B5CF6, gray #6B7280)
- Uses `useUpdateHighlightLabelApiV1HighlightLabelsStyleIdPatch` for mutations
- Invalidates book details + highlight labels queries after success
- Scope: book-specific only (no global defaults UI for now)

### HighlightLabelsList

**File:** `frontend/src/pages/BookPage/navigation/HighlightLabelsList.tsx`

Sidebar section for filtering highlights by label.

- **Props:** `bookId: number`, `selectedLabelId?: number | null`, `onLabelClick: (labelId: number | null) => void`, `hideTitle?: boolean`
- Calls `useGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGet(bookId)`
- Only renders when the book has 2 or more distinct labels
- Section header with palette/color icon and "Labels" title (hideable via `hideTitle`)
- Each label shown as a `Chip` with `backgroundColor` from `ui_color`
- Chip text: `label` if set, otherwise fallback display like "Yellow / Lighten"
- Shows highlight count as suffix
- Clicking a chip toggles `selectedLabelId` (same pattern as tag selection)

## Layout Integration

### HighlightCard footer

Label dot/chip placed in the footer between the metadata row (date, page, icons) and the tag chips:

```
❝ "The highlighted text..."

  📅 May 12, 2025 • Page 42 🔖 📝
  [colored dot/chip]  [tag chips...]
```

### HighlightViewModal

Label dot/chip placed inline in the metadata line, after date and page. Clickable to open the LabelEditorPopover:

```
❝ "The highlighted text..."
📅 May 12, 2025 • Page 42  [colored dot/chip]  ← clickable

[Toolbar]
[Tag input]
[Note]
[Flashcards]
```

### Desktop sidebar (left column)

`HighlightLabelsList` placed below `HighlightTagsList`:

```
LEFT COLUMN (280px):
  HighlightTagsList
  HighlightLabelsList  ← only shown when 2+ labels
```

### Mobile

`HighlightLabelsList` appended below `HighlightTagsList` inside the existing Tags bottom drawer. No new bottom navigation button needed.

### URL state

New `labelId` search param added alongside existing `tagId`. Managed in `HighlightsTab` with same pattern as `selectedTagId`. Filtering function: keep only highlights where `highlight.label?.highlight_style_id === selectedLabelId`.

## Color Palette

Predefined palette for the CirclePicker (~16 colors):

| Color | Hex |
|-------|-----|
| Yellow (KOReader) | #F59E0B |
| Green (KOReader) | #10B981 |
| Blue (KOReader) | #3B82F6 |
| Red (KOReader) | #EF4444 |
| Orange (KOReader) | #F97316 |
| Olive (KOReader) | #84CC16 |
| Cyan (KOReader) | #06B6D4 |
| Purple (KOReader) | #8B5CF6 |
| Gray (KOReader) | #6B7280 |
| Pink | #EC4899 |
| Rose | #F43F5E |
| Teal | #14B8A6 |
| Indigo | #6366F1 |
| Amber | #F59E0B |
| Emerald | #059669 |
| Slate | #475569 |

## Decisions

- **Scope:** Book-specific labels only. No global defaults UI for now.
- **Dot vs chip:** Colored dot when no label text, colored chip when label text is set.
- **Editor:** Popover anchored to dot/chip, with text input + CirclePicker.
- **Sidebar:** Separate "Labels" section below "Tags", only shown when 2+ labels exist.
- **Mobile:** Labels in Tags bottom drawer, below tags.
- **Color picker:** Predefined palette (~16 colors) using react-color's CirclePicker.
