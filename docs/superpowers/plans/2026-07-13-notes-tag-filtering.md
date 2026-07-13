# Notes Tag Filtering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add single-tag filtering to the Notes tab, matching the Highlights/Flashcards tag-filter UX on both desktop and mobile, reusing existing components.

**Architecture:** All changes live in `frontend/src/pages/BookPage/Notes/NotesPage.tsx`. Notes filtering is already server-side via the `highlight_tag_id` query param, so the work is UI wiring: hold the selected tag in local state synced to the `tagId` URL search param, feed it into the notes query, render `HighlightTagsList` in the desktop left sidebar (via `leftSidebarEl` portal) and in a mobile `FilterDrawer` opened by a `FilterFab`.

**Tech Stack:** React, TypeScript, MUI, TanStack Router, `react-dom` `createPortal`. Reused components: `HighlightTagsList`, `FilterDrawer`/`FilterTab`, `FilterFab`.

## Global Constraints

- The frontend has **no test framework** (no vitest). The verification cycle for every task is: `cd frontend && npm run type-check` (expect no errors) and `npm run lint` (expect 0 warnings/errors), plus the manual check described in the task.
- Type checker is **pyright/tsc**, never mypy. Lint is eslint with `--max-warnings 0`; formatter is prettier.
- Follow the existing `FlashcardsPage` pattern exactly (`src/pages/BookPage/Flashcards/FlashcardsPage.tsx`) — it is the reference implementation for this wiring.
- Single-tag selection only. Show all book tags (`book.highlight_tags` / `book.highlight_tag_groups`) with `hideEmptyGroups`. No backend changes.
- Post-edit hooks auto-run lint/type-check after each Edit/Write — read their output.

---

## Reference: current `NotesPage.tsx`

The file today (abridged to the parts that change):

```tsx
export const NotesPage = () => {
  const { book } = useBookPage();
  const navigate = useNavigate({ from: '/book/$bookId/notes' });
  const { kind, chapterId, tagId } = useSearch({ from: '/book/$bookId/notes' });

  const params: GetNotesForBookApiV1BooksBookIdNotesGetParams = {
    kind: (kind as NoteKindValue | undefined) ?? undefined,
    chapter_id: chapterId,
    highlight_tag_id: tagId,
  };
  const { data, isLoading, isError } = useGetNotesForBookApiV1BooksBookIdNotesGet(book.id, params);
  const noteModals = useNoteModals();
  // ...
```

`useBookPage()` also exposes `isDesktop`, `leftSidebarEl`, and `fabContainerEl` (confirmed in `BookPageContext.tsx`), currently unused by `NotesPage`. `book.highlight_tags` and `book.highlight_tag_groups` exist (used by `HighlightsPage`/`FlashcardsPage`).

---

### Task 1: Selected-tag state, URL sync, and tag-aware empty message

Wire a `selectedTagId` state synced to the `tagId` search param, feed it into the notes query, add the `handleTagClick` callback that updates state + URL, and make the empty message tag-aware. No visible tag UI yet — this task is verified by editing the URL directly.

**Files:**
- Modify: `frontend/src/pages/BookPage/Notes/NotesPage.tsx`

**Interfaces:**
- Consumes: `useBookPage()` → `{ book, isDesktop, leftSidebarEl, fabContainerEl }`; `useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, params)`; the `tagId` search param from `useSearch({ from: '/book/$bookId/notes' })`.
- Produces (used by Tasks 2 & 3): `selectedTagId: number | undefined`, `handleTagClick: (newTagId: number | null) => void`.

- [ ] **Step 1: Add React imports**

At the top of `NotesPage.tsx`, add `useEffect` and `useState` to the (currently absent) React import. Insert this import line after the existing `@tanstack/react-router` import:

```tsx
import { useEffect, useState } from 'react';
```

- [ ] **Step 2: Add state and URL sync inside `NotesPage`**

Replace the opening of the component:

```tsx
export const NotesPage = () => {
  const { book } = useBookPage();
  const navigate = useNavigate({ from: '/book/$bookId/notes' });
  const { kind, chapterId, tagId } = useSearch({ from: '/book/$bookId/notes' });

  const params: GetNotesForBookApiV1BooksBookIdNotesGetParams = {
    kind: (kind as NoteKindValue | undefined) ?? undefined,
    chapter_id: chapterId,
    highlight_tag_id: tagId,
  };
```

with:

```tsx
export const NotesPage = () => {
  const { book, isDesktop, leftSidebarEl, fabContainerEl } = useBookPage();
  const navigate = useNavigate({ from: '/book/$bookId/notes' });
  const { kind, chapterId, tagId } = useSearch({ from: '/book/$bookId/notes' });

  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(tagId);

  useEffect(() => {
    setSelectedTagId(tagId);
  }, [tagId]);

  const params: GetNotesForBookApiV1BooksBookIdNotesGetParams = {
    kind: (kind as NoteKindValue | undefined) ?? undefined,
    chapter_id: chapterId,
    highlight_tag_id: selectedTagId,
  };
```

Note: `isDesktop`, `leftSidebarEl`, and `fabContainerEl` are destructured now but only consumed in Tasks 2–3. That would trip the `--max-warnings 0` lint as unused, so **also complete Steps 3–4 in this same task before running lint** — the empty-message change does not use them, so keep them out until Task 2 if you are committing Task 1 standalone. To keep Task 1 lint-clean on its own, destructure only what Task 1 uses:

```tsx
  const { book } = useBookPage();
```

and defer adding `isDesktop, leftSidebarEl, fabContainerEl` to Task 2, Step 1.

- [ ] **Step 3: Add the `handleTagClick` callback**

Immediately after the existing `handleKindFilter` function, add:

```tsx
  const handleTagClick = (newTagId: number | null) => {
    setSelectedTagId(newTagId || undefined);
    void navigate({
      search: (prev) => ({ ...prev, tagId: newTagId || undefined }),
      replace: true,
    });
  };
```

- [ ] **Step 4: Make the empty message tag-aware**

Replace the empty-state block:

```tsx
      {!isLoading && !isError && notes.length === 0 && (
        <Typography color="text.secondary">
          No notes yet. Create notes about characters, terms, and concepts as you read.
        </Typography>
      )}
```

with:

```tsx
      {!isLoading && !isError && notes.length === 0 && (
        <Typography color="text.secondary">
          {selectedTagId
            ? 'No notes found with the selected tag.'
            : 'No notes yet. Create notes about characters, terms, and concepts as you read.'}
        </Typography>
      )}
```

- [ ] **Step 5: Type-check and lint**

Run:

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: no type errors, 0 lint warnings. (`handleTagClick` is not yet referenced by JSX — if eslint flags it as unused, that is expected and resolved in Task 2/3; if you commit Task 1 standalone, temporarily reference it is unnecessary — instead land Task 2 in the same commit. See Step 6.)

- [ ] **Step 6: Manual check + commit**

Manual: run `npm run dev`, open a book's Notes tab, and append `?tagId=<id>` (an id of a tag on some highlight) to the URL. The notes list should re-fetch filtered to that tag; with a tag that has no notes, the "No notes found with the selected tag." message shows. Removing the param restores the full list.

Because `handleTagClick` is only consumed by the UI added in Tasks 2–3, commit Tasks 1–3 together (recommended) OR, if committing incrementally, land Task 2 before running the lint gate so `handleTagClick` has a consumer. When ready:

```bash
git add frontend/src/pages/BookPage/Notes/NotesPage.tsx
git commit -m "Notes: tag filter state synced to tagId search param (#396)"
```

---

### Task 2: Desktop tag sidebar

Render `HighlightTagsList` in the desktop left sidebar via a `createPortal` into `leftSidebarEl`, mirroring `FlashcardsSidebar`.

**Files:**
- Modify: `frontend/src/pages/BookPage/Notes/NotesPage.tsx`

**Interfaces:**
- Consumes: `selectedTagId` and `handleTagClick` (Task 1); `isDesktop`, `leftSidebarEl` from `useBookPage()`; `book.highlight_tags`, `book.highlight_tag_groups`.

- [ ] **Step 1: Ensure layout hooks are destructured**

Confirm the component destructures the layout fields (add any missing):

```tsx
  const { book, isDesktop, leftSidebarEl, fabContainerEl } = useBookPage();
```

(`fabContainerEl` is consumed in Task 3; if committing Task 2 alone, destructure only `book, isDesktop, leftSidebarEl` here and add `fabContainerEl` in Task 3.)

- [ ] **Step 2: Add imports**

Add `Divider` to the existing MUI import, and add the portal + component imports. The MUI import becomes:

```tsx
import { Box, Button, Divider, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
```

Add these imports (place the `createPortal` import after the router import, and the component imports alongside the existing `./NoteCard` group):

```tsx
import { createPortal } from 'react-dom';

import { HighlightTagsList } from '../navigation/HighlightTagsList.tsx';
```

- [ ] **Step 3: Portal the sidebar into `leftSidebarEl`**

As the first child inside the top-level `<Box>` returned by `NotesPage` (before the toolbar `<Box>`), add:

```tsx
      {isDesktop &&
        leftSidebarEl &&
        createPortal(
          <>
            <Divider sx={{ mb: 4 }} />
            <HighlightTagsList
              tags={book.highlight_tags}
              tagGroups={book.highlight_tag_groups}
              bookId={book.id}
              selectedTag={selectedTagId}
              onTagClick={handleTagClick}
              hideEmptyGroups
            />
          </>,
          leftSidebarEl
        )}
```

- [ ] **Step 4: Type-check and lint**

Run:

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: no type errors, 0 lint warnings.

- [ ] **Step 5: Manual check + commit**

Manual: on a desktop-width viewport, the Notes tab left sidebar shows the tag list. Clicking a tag filters the notes list and sets `?tagId=` in the URL; clicking the selected tag again clears the filter. Commit (skip if bundling with Task 1):

```bash
git add frontend/src/pages/BookPage/Notes/NotesPage.tsx
git commit -m "Notes: desktop tag-filter sidebar (#396)"
```

---

### Task 3: Mobile filter FAB + drawer

Add the mobile `FilterFab` (portaled into `fabContainerEl`) and a single-tab `FilterDrawer` containing `HighlightTagsList`, matching the Flashcards mobile pattern.

**Files:**
- Modify: `frontend/src/pages/BookPage/Notes/NotesPage.tsx`

**Interfaces:**
- Consumes: `selectedTagId`, `handleTagClick` (Task 1); `isDesktop`, `fabContainerEl` (Task 2/`useBookPage`); `FilterFab`, `FilterDrawer`, `FilterTab`.

- [ ] **Step 1: Add imports and drawer-open state**

Add these imports alongside the existing component imports:

```tsx
import { FilterFab } from '../common/FilterFab.tsx';
import { FilterDrawer, type FilterTab } from '../navigation/FilterDrawer.tsx';
```

Add drawer state near the other `useState` calls in `NotesPage`:

```tsx
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
```

- [ ] **Step 2: Build the single Tags tab**

After `const notes = data?.notes ?? [];`, add:

```tsx
  const filterTabs: FilterTab[] = [
    {
      label: 'Tags',
      content: (
        <HighlightTagsList
          tags={book.highlight_tags}
          tagGroups={book.highlight_tag_groups}
          bookId={book.id}
          selectedTag={selectedTagId}
          onTagClick={(id) => {
            handleTagClick(id);
            setFilterDrawerOpen(false);
          }}
          hideTitle
          hideEmptyGroups
        />
      ),
    },
  ];
```

- [ ] **Step 3: Render the FAB portal and drawer**

Just before the closing `<NoteModals controller={noteModals} />` line, add:

```tsx
      {!isDesktop &&
        fabContainerEl &&
        createPortal(
          <FilterFab
            filterEnabled={!!selectedTagId}
            onClick={() => setFilterDrawerOpen(true)}
          />,
          fabContainerEl
        )}
      {!isDesktop && (
        <FilterDrawer
          open={filterDrawerOpen}
          onClose={() => setFilterDrawerOpen(false)}
          tabs={filterTabs}
        />
      )}
```

- [ ] **Step 4: Type-check and lint**

Run:

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: no type errors, 0 lint warnings.

- [ ] **Step 5: Manual check + commit**

Manual: at a mobile-width viewport, the filter FAB appears; it is highlighted (primary color) when a tag is active. Tapping it opens the drawer with a "Tags" tab; selecting a tag filters the notes list, closes the drawer, and sets `?tagId=`. Commit (skip if bundling with Tasks 1–2):

```bash
git add frontend/src/pages/BookPage/Notes/NotesPage.tsx
git commit -m "Notes: mobile tag-filter FAB and drawer (#396)"
```

---

## Self-Review Notes

- **Spec coverage:** state/URL sync (Task 1), desktop sidebar (Task 2), mobile FAB+drawer (Task 3), tag-aware empty state (Task 1), all-book-tags with `hideEmptyGroups` (Tasks 2–3), single-tag selection (throughout). No backend work (unchanged). All spec sections covered.
- **Unused-symbol caution:** the `--max-warnings 0` lint means a symbol destructured/defined before its consumer exists will fail the gate. The plan flags this at each step — either bundle Tasks 1–3 into one commit (recommended, single small file) or add each layout field / callback only in the task that consumes it. The final state destructures `{ book, isDesktop, leftSidebarEl, fabContainerEl }` and uses every one.
- **Type consistency:** `handleTagClick` signature `(newTagId: number | null) => void` matches `HighlightTagsList`'s `onTagClick` prop and `FlashcardsPage`'s usage. `selectedTag` prop takes `number | undefined`.
