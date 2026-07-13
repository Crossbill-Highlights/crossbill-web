# Notes: tag filtering on the notes list

**Issue:** [crossbill-web#396](https://github.com/Crossbill-Highlights/crossbill-web/issues/396) — part of the Book Notes feature follow-ups (PR #389).

## Goal

Add tag filtering to the Notes tab, working the same way as the Highlights view's
tag filtering. The user can filter the notes list by a single highlight tag, with
identical interaction/UX to the existing Highlights and Flashcards filters on both
desktop and mobile, reusing the existing tag-filter components.

## Context

- Notes filtering is already **server-side**: the list endpoint accepts
  `GET /api/v1/books/{book_id}/notes?highlight_tag_id=<id>`, exposed as the
  `highlight_tag_id` param on `useGetNotesForBookApiV1BooksBookIdNotesGet`.
- The notes route (`src/routes/book.$bookId/notes.tsx`) already validates a `tagId`
  search param, and `NotesPage` already threads it into the query params.
- `BookPageContext` exposes `isDesktop`, `leftSidebarEl`, and `fabContainerEl` — the
  same layout hooks the Flashcards view uses for its desktop sidebar and mobile
  filter drawer. `NotesPage` currently leaves both portals empty.
- Reusable components already exist:
  - `HighlightTagsList` (`src/pages/BookPage/navigation/HighlightTagsList.tsx`) —
    the tag list with grouping, drag-to-organize, `selectedTag` / `onTagClick`,
    and `hideTitle` / `hideEmptyGroups` props.
  - `FilterDrawer` / `FilterTab` (`src/pages/BookPage/navigation/FilterDrawer.tsx`).
  - `FilterFab` (`src/pages/BookPage/common/FilterFab.tsx`).

**Closest analog:** `FlashcardsPage` — it wires all of the above together. The main
difference is that Flashcards filters client-side while Notes filters server-side,
which simplifies the Notes work: the selected tag only needs to flow into the
`tagId` search param and the query re-fetches automatically.

## Decisions

- **Single-tag selection** — matches the existing Highlights/Flashcards UX (one
  active tag at a time) and the backend's single `highlight_tag_id` param. No
  multi-select.
- **All book tags shown** — pass `book.highlight_tags` / `book.highlight_tag_groups`
  with `hideEmptyGroups`, same as the Highlights view. No extra query to compute
  which tags have notes.

## Design

### State & URL (in `NotesPage`)

- Add `selectedTagId` state, initialized from the `tagId` search param, kept in sync
  via `useEffect` on `tagId` (same pattern as `FlashcardsPage`).
- Add a `handleTagClick(newTagId: number | null)` callback that sets the state and
  writes the URL:
  `navigate({ search: (prev) => ({ ...prev, tagId: newTagId || undefined }), replace: true })`.
- Feed `selectedTagId` into `params.highlight_tag_id` (replacing the direct read of
  `tagId`), so the notes query re-fetches when the selection changes.

### Desktop

Portal a small sidebar component (leading `Divider` + `HighlightTagsList`) into
`leftSidebarEl`, guarded by `isDesktop && leftSidebarEl`, mirroring `FlashcardsSidebar`:

```
<HighlightTagsList
  tags={book.highlight_tags}
  tagGroups={book.highlight_tag_groups}
  bookId={book.id}
  selectedTag={selectedTagId}
  onTagClick={handleTagClick}
  hideEmptyGroups
/>
```

### Mobile

- Portal a `FilterFab` into `fabContainerEl` (guarded by `fabContainerEl` and rendered
  in the non-desktop branch), with `filterEnabled={!!selectedTagId}`, opening a
  `FilterDrawer`.
- The drawer has a **single "Tags" tab** rendering `HighlightTagsList` with
  `hideTitle` and `hideEmptyGroups`. Selecting a tag applies it via `handleTagClick`
  and closes the drawer. (Unlike Flashcards, Notes has no chapter-nav sidebar today,
  so there is only the one tab.)

### Empty state

When a tag is selected but the filtered result is empty, show a tag-aware message
("No notes found with the selected tag.") instead of the generic "No notes yet…".

## Out of scope

- Multi-tag selection.
- Chapter filtering changes (the `chapterId` param is untouched).
- Any backend work — the endpoint and search param already exist.

## Testing / verification

- `cd frontend && npm run type-check` and `npm run lint` pass.
- Manual: on a book with tagged highlights and notes, selecting a tag (desktop
  sidebar and mobile drawer) filters the notes list and updates the URL; clearing it
  restores the full list; deep-linking with `?tagId=` pre-selects the tag.
