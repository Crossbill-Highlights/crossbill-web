# Blurhash Cover Placeholders

## Problem

Book cover images on the frontpage load slowly on uncached browsers, causing visible layout shifts and a bare/ugly appearance while images load.

## Solution

Add blurhash-based placeholder images that display instantly while the real cover loads, then crossfade to the actual image. Additionally, resize cover images at upload time to a reasonable target size (300x420) to improve load times.

## Backend Changes

### New Database Column

Add a nullable `cover_blurhash` column (`String(40)`) to the Book model. No backfill migration needed — books without a blurhash will use a hardcoded fallback on the frontend.

### Image Processing at Upload Time

When a cover is extracted from an EPUB during upload (`_extract_and_save_cover` in `EbookUploadUseCase`):

1. Open the raw cover bytes with Pillow
2. Resize to fit within 300x420 while maintaining aspect ratio (use `Image.LANCZOS` resampling)
3. Save as JPEG (quality ~85)
4. Generate a blurhash string from the resized image using the `blurhash-python` library
5. Store the resized JPEG via `file_repository.save_cover()`
6. Store the blurhash string on the Book domain entity

The image processing logic should live in a domain service or infrastructure service (not in the use case directly) since it involves image manipulation.

### New Dependencies

- `Pillow` — image resizing
- `blurhash-python` — blurhash encoding

### Domain Entity Changes

Add `cover_blurhash: str | None = None` field to `Book` domain entity. Add a method to set it (or extend `set_cover_file` to also accept the blurhash).

### ORM Model Changes

Add `cover_blurhash` mapped column to the Book ORM model in the infrastructure layer. Update ORM-to-domain and domain-to-ORM conversion.

### API Schema Changes

Add `cover_blurhash: str | None` to:
- `BookWithHighlightCount`
- `EreaderBookMetadata`
- Any other schemas that include `cover_file`

### Database Migration

Single Alembic migration adding the nullable `cover_blurhash` column to the `books` table.

## Frontend Changes

### New Dependency

- `react-blurhash` — renders blurhash strings to canvas elements

### BookCover Component Updates

Add a `blurhash: string | null` prop. Behavior:

1. **Has cover_file + blurhash**: Show blurhash canvas immediately, load image in background, crossfade on load
2. **Has cover_file + no blurhash**: Show a hardcoded neutral fallback blurhash, same crossfade behavior
3. **No cover_file**: Keep current BookCoverIcon placeholder (no change)

The crossfade uses CSS opacity transition on the `<img>` element (start at 0, transition to 1 on load).

A `FALLBACK_BLURHASH` constant is defined in the component file — a neutral gray/beige blurhash string.

### BookCard Updates

Pass `book.cover_blurhash` through to `BookCover`.

### API Type Regeneration

Regenerate TypeScript types from the updated OpenAPI schema to include `cover_blurhash`.

## Architecture Notes

- Image processing code belongs in the infrastructure layer (it depends on Pillow/blurhash libraries)
- The domain entity only stores the blurhash string — no library dependencies in the domain layer
- The use case orchestrates: extract cover -> process image (resize + blurhash) -> save file -> update entity
