# Position Index: Design Prompt

## Problem

We need reliable position comparison for entities (highlights, reading sessions, chapters) within EPUB books. The current approach parses KOReader xpoint strings and attempts to compare them structurally, but this is fundamentally unreliable because XPath indices are **per-element-type** within their parent.

### Why xpoint comparison fails

An xpoint like `/body/DocFragment[14]/body/div[1]/p[3]/text().50` means "the 3rd `<p>` child of `div[1]`" - not "the 3rd child overall." Given this HTML:

```html
<div>
  <h2>Title</h2>         <!-- h2[1], actual position: 1st child -->
  <p>Paragraph 1</p>     <!-- p[1],  actual position: 2nd child -->
  <blockquote>...</blockquote>  <!-- blockquote[1], 3rd child -->
  <p>Paragraph 2</p>     <!-- p[2],  actual position: 4th child -->
</div>
```

From xpoints alone, we cannot determine where `blockquote[1]` falls relative to `p[1]` and `p[2]`. When a reading session ranges from `div[1]/p[1]` to `div[1]/p[3]`, we have no way to know whether `div[1]/blockquote[1]` is inside or outside that range without parsing the actual EPUB DOM.

The immediate symptom: a reading session covering pages 73-75 was incorrectly linked to ~15 highlights from pages 35-44 because the xpoint containment check produced false positives when the session's start and end xpoints diverged into different element types at the same depth.

### Current workaround

We applied a targeted fix: `XPoint.compare_to()` now returns `None` (incomparable) when element names differ at the same depth, and `XPointRange.contains()` returns `False` when comparison is inconclusive. The highlight-to-session matching also prioritizes page-based matching over xpoint matching. This prevents the worst false positives but means xpoint-based matching silently gives up whenever the DOM structure is heterogeneous - which is common in real EPUBs.

## Proposed Solution: Document-Order Position Index

Introduce a numeric **position** value derived by walking the actual EPUB DOM in document order. This position is an integer that reflects the true sequential order of elements in the book, enabling reliable `O(1)` comparisons.

### Core idea

When an EPUB is available, walk its DOM in document order and assign a sequential integer to each element node. Store this position on entities that need position comparison (highlights, reading sessions). For PDFs, the page number already serves as a reliable position.

### What entities need positions

- **Highlights**: need a `position` (derived from their `start_xpoint`)
- **Reading sessions**: need `start_position` and `end_position` (derived from their start/end xpoints)
- **Chapters**: already have `chapter_number` and `start_xpoint`/`end_xpoint`, could also benefit from `start_position`/`end_position`

### How positions would be computed

1. Parse the EPUB file using `ebooklib` + `lxml` (capabilities already exist in `EpubTocParserService` and `EpubTextExtractionService`)
2. Walk the spine items (DocFragments) in order
3. Within each spine item, walk the DOM tree in document order
4. Assign a monotonically increasing integer to each element node
5. For a given xpoint, resolve it to its element in the DOM and return the assigned position

### Where positions would be used

The primary use case is **highlight-to-session matching** during reading session upload (`ReadingSessionUploadUseCase._find_matching_highlights`). Instead of comparing xpoint strings:

```python
# Current (unreliable)
session.start_xpoint.contains(highlight.xpoints.start)

# Proposed (reliable)
session.start_position <= highlight.position <= session.end_position
```

This would also enable reliable position-based ordering of highlights within a session (currently done via `ORDER BY page, start_xpoint` which is a text sort on xpoint strings).

## Current Architecture Context

The following summarizes the relevant parts of the codebase for designing the implementation.

### Domain entities with position data

**Highlight** (`backend/src/domain/reading/entities/highlight.py`):
- `xpoints: XPointRange | None` - parsed from `start_xpoint`/`end_xpoint` strings
- `page: int | None` - page number from KOReader
- `chapter_id: ChapterId | None` - resolved during upload via `chapter_number`

**ReadingSession** (`backend/src/domain/reading/entities/reading_session.py`):
- `start_xpoint: XPointRange | None` - session's reading range (confusingly named, it's a range)
- `start_page: int | None`, `end_page: int | None`

**Chapter** (`backend/src/domain/library/entities/chapter.py`):
- `chapter_number: int | None` - order from TOC
- `start_xpoint: str | None`, `end_xpoint: str | None` - chapter boundaries

### EPUB parsing infrastructure

**`EpubTocParserService`** (`backend/src/infrastructure/library/services/epub_toc_parser_service.py`):
- Parses EPUB TOC, resolves hrefs to xpoint strings
- Builds spine-to-index mapping (DocFragment indices)
- Has lxml DOM access to spine items

**`EpubTextExtractionService`** (`backend/src/infrastructure/library/services/epub_text_extraction_service.py`):
- Extracts text between xpoint positions
- Navigates DOM using lxml, handles cross-fragment ranges
- Already resolves xpoints to DOM elements

### Data flow

**Highlight upload** (`backend/src/application/reading/use_cases/highlights/highlight_upload_use_case.py`):
- KOReader sends: `text`, `start_xpoint`, `end_xpoint`, `page`, `chapter_number`, `note`, `datetime`
- Use case resolves `chapter_number` to `chapter_id`, parses xpoints, deduplicates, bulk saves

**Reading session upload** (`backend/src/application/reading/use_cases/reading_sessions/reading_session_upload_use_case.py`):
- KOReader sends: `start_time`, `end_time`, `start_xpoint`, `end_xpoint`, `start_page`, `end_page`, `device_id`
- After creating sessions, links existing highlights to sessions via `_find_matching_highlights()`

**EPUB upload** (`backend/src/application/library/use_cases/ebook_upload_use_case.py`):
- Saves EPUB file to disk, parses TOC, syncs chapters
- Book's `file_path` and `file_type` are set
- Chapters get `start_xpoint`/`end_xpoint` from TOC parsing

### Database schema (relevant tables)

- `highlights`: columns include `start_xpoint TEXT`, `end_xpoint TEXT`, `page INT`, `chapter_id INT FK`
- `reading_sessions`: columns include `start_xpoint TEXT`, `end_xpoint TEXT`, `start_page INT`, `end_page INT`
- `chapters`: columns include `start_xpoint TEXT`, `end_xpoint TEXT`, `chapter_number INT`
- `reading_session_highlights`: join table `(reading_session_id, highlight_id, created_at)`

### XPoint value objects

**`XPoint`** (`backend/src/domain/common/value_objects/xpoint.py`):
- `doc_fragment_index: int | None` - 1-based spine item index
- `xpath: str` - e.g., `/body/div[2]/p[1]`
- `text_node_index: int` - 1-based text node within element
- `char_offset: int` - 0-based character offset

**`XPointRange`**: `start: XPoint`, `end: XPoint` with `contains(point)` method

### Architecture rules (from CLAUDE.md)

- **Domain layer** must not depend on ORM, infrastructure, or Pydantic
- **Application layer** works with domain entities, uses repository protocols
- **Infrastructure layer** owns ORM models and conversions
- Position computation would likely be a **domain service** (pure logic) that takes parsed DOM data, or an **infrastructure service** if it needs direct EPUB file access via ebooklib/lxml

## Design Considerations

1. **Timing**: Positions can only be computed when the EPUB file is available. Highlights and sessions may be uploaded before the EPUB. The design needs to handle deferred position computation (backfilling when the EPUB arrives).

2. **Xpoints remain the source of truth**: Positions are a derived index. Xpoints and page numbers should still be stored. If the EPUB is re-uploaded or reprocessed, positions can be recomputed from xpoints.

3. **PDFs**: For PDF books, `page` already serves as a reliable position. The position index is primarily needed for EPUBs.

4. **Storage**: Positions could be columns on existing tables (simpler queries, but need updating on reprocessing) or a separate lookup table (single update point, but requires joins).

5. **Granularity**: Element-level positions are likely sufficient for matching highlights to sessions. Character-level precision within an element is rarely needed for this use case.

6. **Recomputation**: When the EPUB is re-uploaded or the position computation logic changes, all positions for that book's entities need recomputation. This should be efficient (batch update).

7. **The existing `EpubTocParserService` and `EpubTextExtractionService`** already have lxml DOM traversal capabilities that could be extended or reused for position index building.
