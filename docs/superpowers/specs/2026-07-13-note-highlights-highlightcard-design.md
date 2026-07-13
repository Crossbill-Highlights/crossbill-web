# Notes: reuse `HighlightCard` in the note detail's Highlights tab

**Context:** Part of the Book Notes feature follow-ups. Unrelated to the tag-filtering
work on the same branch.

## Problem

The note detail modal (`NoteViewModal` → `NoteLinkTabs`) renders a note's linked
highlights with a bespoke `List`/`ListItemButton` row and a hand-rolled text-preview
helper (`formatHighlightPreview`). The app already has a canonical highlight component,
`HighlightCard` (`frontend/src/pages/BookPage/Highlights/HighlightCard.tsx`), used e.g.
by `ChapterDetailDialog/HighlightsSection.tsx`. The note detail should use that same
component instead of its own list, for visual and behavioural consistency.

## Approach

Resolve full `Highlight` objects on the **frontend from the already-loaded book
context** — no backend change.

`HighlightCard` requires the full `Highlight` shape (`label`, `datetime`, `page`,
`note`, `flashcards`, `highlight_tags`, `text`). The note detail endpoint only returns
lightweight `NoteLinkedHighlight` summaries (`{id, text}`). However, `NoteViewModal`
already consumes `useBookPage().book`, whose `chapters[].highlights` are the exact full
`Highlight` objects `HighlightsSection` feeds to `HighlightCard`. So we look the full
objects up by id rather than enriching the API.

This was chosen over a backend enrichment of `GET /notes/{id}` because: the note **list**
cards (`NoteCard`) don't render highlights at all (so no payload benefit to the list),
the book context already holds HighlightCard-ready highlights, and it is far less code
(no repo/label-resolution/N+1 work, no orval regen).

**Accepted trade-off:** a linked highlight that is not present in the loaded book
chapters would not render. In practice a note can only link highlights belonging to its
book, and the book detail loads all of them, so this should not occur; such misses are
filtered out silently (consistent with the current soft-deleted handling).

## Changes

### `NoteViewModal.tsx`

- Build an `id → Highlight` map from `book.chapters.flatMap((c) => c.highlights)`.
- Map the note's displayable highlights (`activeNote.highlights`, which the backend
  already filters to exclude soft-deleted) to their full `Highlight` objects via the map,
  filtering out any ids not found.
- Pass the resulting `Highlight[]` to `NoteLinkTabs` (replacing the `NoteLinkedHighlight[]`
  it passes today).
- `handleOpenHighlight` / `handleOpenChapter` navigation is unchanged.

### `NoteLinkTabs.tsx`

- Change the `highlights` prop type from `NoteLinkedHighlight[]` to `Highlight[]`.
- Render the Highlights tab as a `<Stack component="ul">` of `HighlightCard`s (mirroring
  `HighlightsSection`), each `<HighlightCard highlight={h} onOpenModal={onOpenHighlight} />`.
- Remove the now-unused `formatHighlightPreview` helper, `PREVIEW_WORD_COUNT`, and the
  `QuoteIcon` / `List` / `ListItemButton` / `ListItemText` imports (only if they become
  unused — the Chapters tab still uses `List`/`ListItemButton`/`ListItemText`).
- The **Chapters tab is unchanged** (still a `NoteLinkedChapter` list).

### Behaviour

- Clicking a highlight card calls `onOpenHighlight(id)` — navigates to the highlights
  page deep link and the note modal closes — identical to today.
- `HighlightCard`'s optional `bookmark` prop is omitted (no bookmark map is readily
  available in the note modal; not essential here).

## Out of scope

- No backend changes; no orval regeneration.
- Chapters tab behaviour/appearance.
- Opening a `HighlightViewModal` in place (navigation behaviour is preserved).
- Bookmark indicators on the cards.

## Verification

- `cd frontend && npm run type-check` (no errors) and `npm run lint` (`--max-warnings 0`).
- Manual: open a note with linked highlights; the Highlights tab shows `HighlightCard`s
  identical to the chapter detail dialog; clicking one navigates to that highlight; a note
  with only chapters still shows just the Chapters tab.
