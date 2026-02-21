# Highlight Labels Design

## Overview

Highlight labels allow users to assign meaningful names and custom UI colors to the highlight styles (color + drawing style) that KOReader and other reading devices use. Each unique combination of device color and device style gets its own record that users can customize with a label (e.g. "Criticism", "Key Argument") and a UI color.

Labels are book-specific with global defaults. Users can set global defaults that apply across all books, and override them per-book.

## Database Schema

### New table: `highlight_styles`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | SERIAL PK | no | |
| `user_id` | int FK → users | no | ON DELETE CASCADE |
| `book_id` | int FK → books | yes | NULL = global default. ON DELETE CASCADE |
| `device_color` | VARCHAR(50) | yes | Device highlight color (e.g. "green", "gray"). NULL = applies to any color |
| `device_style` | VARCHAR(50) | yes | Device drawing style (e.g. "lighten", "strikethrough"). NULL = applies to any style |
| `label` | VARCHAR(255) | yes | User-assigned label |
| `ui_color` | VARCHAR(20) | yes | User-chosen CSS color (e.g. "#ff5733") |
| `created_at` | TIMESTAMPTZ | no | DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | no | DEFAULT NOW() |

### Row types determined by NULLs

| `book_id` | `device_color` | `device_style` | Meaning |
|-----------|----------------|-----------------|---------|
| set | set | set | Combination-level, book-specific — highlights FK here |
| set | set | NULL | Individual color label for a book |
| set | NULL | set | Individual style label for a book |
| NULL | set | set | Global default for a combination |
| NULL | set | NULL | Global default for a color |
| NULL | NULL | set | Global default for a style |

### Partial unique indexes

6 partial unique indexes enforce uniqueness across NULL combinations (PostgreSQL NULL != NULL):

```sql
-- Combination-level, book-specific (highlights FK here)
CREATE UNIQUE INDEX uq_hs_all
  ON highlight_styles (user_id, book_id, device_color, device_style)
  WHERE book_id IS NOT NULL AND device_color IS NOT NULL AND device_style IS NOT NULL;

-- Color-only, book-specific
CREATE UNIQUE INDEX uq_hs_book_color
  ON highlight_styles (user_id, book_id, device_color)
  WHERE book_id IS NOT NULL AND device_color IS NOT NULL AND device_style IS NULL;

-- Style-only, book-specific
CREATE UNIQUE INDEX uq_hs_book_style
  ON highlight_styles (user_id, book_id, device_style)
  WHERE book_id IS NOT NULL AND device_color IS NULL AND device_style IS NOT NULL;

-- Combination-level, global
CREATE UNIQUE INDEX uq_hs_global_combo
  ON highlight_styles (user_id, device_color, device_style)
  WHERE book_id IS NULL AND device_color IS NOT NULL AND device_style IS NOT NULL;

-- Color-only, global
CREATE UNIQUE INDEX uq_hs_global_color
  ON highlight_styles (user_id, device_color)
  WHERE book_id IS NULL AND device_color IS NOT NULL AND device_style IS NULL;

-- Style-only, global
CREATE UNIQUE INDEX uq_hs_global_style
  ON highlight_styles (user_id, device_style)
  WHERE book_id IS NULL AND device_color IS NULL AND device_style IS NOT NULL;
```

### Changes to `highlights` table

- **Add** `highlight_style_id` INTEGER FK → `highlight_styles(id)` ON DELETE SET NULL
- **Drop** `highlight_style` JSON column

### Migration

Replace existing migration 041 (JSON column approach, not yet merged to main) with a single migration that:

1. Creates the `highlight_styles` table with all columns and partial unique indexes
2. Adds `highlight_style_id` column to `highlights` (nullable initially)
3. Migrates existing data: for each unique `(user_id, book_id, color, style)` in the JSON column, inserts a `highlight_styles` row and updates matching highlights' `highlight_style_id`
4. Drops the `highlight_style` JSON column

## Domain Layer

### HighlightStyle entity (promoted from value object)

The current `HighlightStyle` frozen dataclass value object is promoted to a full `Entity[HighlightStyleId]` since it now has identity, lifecycle, and mutable state.

```python
@dataclass
class HighlightStyle(Entity[HighlightStyleId]):
    id: HighlightStyleId
    user_id: UserId
    book_id: BookId | None          # None = global default
    device_color: str | None        # None = applies to any color
    device_style: str | None        # None = applies to any style
    label: str | None               # user-assigned label
    ui_color: str | None            # user-chosen UI color
    created_at: datetime
    updated_at: datetime
```

Methods:
- `update_label(label: str | None)` — set or clear the label
- `update_ui_color(ui_color: str | None)` — set or clear the UI color
- `is_combination_level() -> bool` — both device fields set
- `is_global() -> bool` — book_id is None
- Factory: `create(user_id, book_id, device_color, device_style)` — for auto-creation on upload
- Factory: `create_with_id(...)` — for reconstitution from DB

### HighlightStyleId value object

New ID type added to `backend/src/domain/common/value_objects/ids.py`.

### Highlight entity change

Replace `highlight_style: HighlightStyle` field with:

```python
highlight_style_id: HighlightStyleId | None
```

The Highlight no longer carries the full style — it references one by ID.

### HighlightStyleResolver domain service

Resolves the effective label and ui_color for a highlight using priority chain:

1. Combination + book (book_id=X, color=Y, style=Z)
2. Color-only + book (book_id=X, color=Y, style=NULL)
3. Style-only + book (book_id=X, color=NULL, style=Z)
4. Combination + global (book_id=NULL, color=Y, style=Z)
5. Color-only + global (book_id=NULL, color=Y, style=NULL)
6. Style-only + global (book_id=NULL, color=NULL, style=Z)
7. No label — fall back to None

## Infrastructure Layer

- New ORM model `HighlightStyle` in `models.py`
- New `HighlightStyleRepository` with `find_or_create(user_id, book_id, device_color, device_style)` for the upload flow
- New `HighlightStyleMapper` for ORM ↔ domain conversion
- Updated `HighlightMapper` to handle `highlight_style_id` FK instead of JSON

## API Layer

### Routes

Routes use the user-facing term "highlight-labels" (not "highlight-styles"). Internal naming stays `HighlightStyle`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/books/{book_id}/highlight-labels` | List all labels for a book (includes resolved labels from global defaults) |
| `PATCH` | `/api/v1/highlight-labels/{id}` | Update label and/or ui_color |
| `GET` | `/api/v1/highlight-labels/global` | List global default labels |
| `POST` | `/api/v1/highlight-labels/global` | Create a global default label |
| `PATCH` | `/api/v1/highlight-labels/global/{id}` | Update a global default label |

### Highlight label response (from `/highlight-labels` endpoints)

```json
{
  "id": 42,
  "device_color": "green",
  "device_style": "lighten",
  "label": "Key Argument",
  "ui_color": "#22c55e",
  "label_source": "book",
  "highlight_count": 12
}
```

- `label_source`: "book", "global", or "none" — tells UI where the effective label came from
- `highlight_count`: number of highlights using this style in this book

### Highlight response change

All highlight response schemas replace the old inline `HighlightStyleResponse(color, style)` with resolved label fields. Highlight responses do NOT include device values (`device_color`, `device_style`):

```json
{
  "highlight_style_id": 42,
  "label": "Key Argument",
  "ui_color": "#22c55e"
}
```

### Upload flow

1. KOReader sends highlights with `color` and `drawer` fields (unchanged)
2. Use case calls repository: `find_or_create(user_id, book_id, device_color=color, device_style=drawer)`
3. Repository upserts — finds existing combination-level row or creates one with `label=None`, `ui_color=None`
4. Highlight is created with `highlight_style_id` pointing to that row
