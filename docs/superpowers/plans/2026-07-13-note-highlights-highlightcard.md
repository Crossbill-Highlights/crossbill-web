# Reuse HighlightCard in Note Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a note's linked highlights in the note detail modal with the shared `HighlightCard` component (as the chapter detail dialog does), instead of the bespoke list, resolving full `Highlight` objects from the already-loaded book context.

**Architecture:** Frontend-only, two files. `NoteViewModal` builds an `id → Highlight` map from `useBookPage().book.chapters[].highlights` and resolves the note's displayable highlights to full `Highlight` objects, passing them to `NoteLinkTabs`. `NoteLinkTabs`'s Highlights tab renders `HighlightCard`s (mirroring `HighlightsSection`); its Chapters tab is unchanged. No backend change, no API/orval regeneration.

**Tech Stack:** React, TypeScript, MUI, TanStack Router. Reused component: `HighlightCard` (`frontend/src/pages/BookPage/Highlights/HighlightCard.tsx`).

## Global Constraints

- The frontend has **no test framework** (no vitest). The verification cycle is: `cd frontend && npm run type-check` (expect no errors) and `npm run lint` (`--max-warnings 0`, expect 0 warnings/errors), plus the manual check in the task.
- Type checker is **tsc/pyright**, never mypy. Lint is eslint `--max-warnings 0`; formatter is prettier.
- No backend changes; no orval regeneration.
- Land the change in **one commit** — the `NoteLinkTabs` prop-type change breaks `NoteViewModal` until it is updated, so any intermediate state fails the type-check/lint gate.
- Preserve current click behaviour: clicking a highlight calls `onOpenHighlight(id)` (navigates to the highlights deep link; the note modal closes). The Chapters tab is untouched.
- Post-edit hooks auto-run lint/type-check after each Edit/Write — read their output.

## Reference: how HighlightsSection uses HighlightCard

`frontend/src/pages/BookPage/Structure/ChapterDetailDialog/HighlightsSection.tsx` renders:

```tsx
<Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
  {highlights.map((highlight) => (
    <li key={highlight.id}>
      <HighlightCard highlight={highlight} bookmark={...} onOpenModal={handleOpenHighlight} />
    </li>
  ))}
</Stack>
```

`HighlightCard`'s props (from `HighlightCard.tsx`):

```tsx
export interface HighlightCardProps {
  highlight: Highlight;                          // full model from '@/api/generated/model'
  bookmark?: Bookmark;                           // optional — omitted here
  onOpenModal?: (highlightId: number) => void;   // called on click
}
```

`book.chapters` (from `useBookPage().book`) is `ChapterWithHighlights[]`; each `chapter.highlights` is `Highlight[]` — the same full objects `HighlightsSection` passes to `HighlightCard`.

---

### Task 1: Render linked highlights with HighlightCard (both files, one commit)

**Files:**
- Modify: `frontend/src/pages/BookPage/Notes/components/NoteLinkTabs.tsx`
- Modify: `frontend/src/pages/BookPage/Notes/NoteViewModal.tsx`

**Interfaces:**
- Consumes: `HighlightCard` (`onOpenModal: (highlightId: number) => void`); `useBookPage().book.chapters[].highlights: Highlight[]`; the note detail's `activeNote.highlights` (lightweight `{id, text}`, already soft-delete-filtered by the backend).
- Produces: `NoteLinkTabs` now takes `highlights: Highlight[]` instead of `NoteLinkedHighlight[]`.

- [ ] **Step 1: Rewrite `NoteLinkTabs.tsx`**

Replace the entire file contents with:

```tsx
import type { Highlight, NoteLinkedChapter } from '@/api/generated/model';
import { HighlightCard } from '@/pages/BookPage/Highlights/HighlightCard.tsx';
import { Box, List, ListItemButton, ListItemText, Stack, Tab, Tabs } from '@mui/material';
import { type ReactElement, useState } from 'react';

interface NoteLinkTabsProps {
  highlights: Highlight[];
  chapters: NoteLinkedChapter[];
  onOpenHighlight: (highlightId: number) => void;
  onOpenChapter: (chapterId: number) => void;
}

const formatTabLabel = (label: string, count: number) =>
  count > 0 ? `${label} (${count})` : label;

/**
 * Tabs listing a note's linked entities (highlights, chapters). The Highlights
 * tab reuses the shared `HighlightCard`; the Chapters tab lists clickable rows.
 * Only tabs whose entity type has items are rendered, mirroring
 * `ChapterDetailDialog`'s tabbed composition.
 */
export const NoteLinkTabs = ({
  highlights,
  chapters,
  onOpenHighlight,
  onOpenChapter,
}: NoteLinkTabsProps) => {
  const tabs = [
    highlights.length > 0 && {
      key: 'highlights',
      label: formatTabLabel('Highlights', highlights.length),
      content: (
        <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
          {highlights.map((highlight) => (
            <li key={highlight.id}>
              <HighlightCard highlight={highlight} onOpenModal={onOpenHighlight} />
            </li>
          ))}
        </Stack>
      ),
    },
    chapters.length > 0 && {
      key: 'chapters',
      label: formatTabLabel('Chapters', chapters.length),
      content: (
        <List disablePadding>
          {chapters.map((chapter) => (
            <ListItemButton key={chapter.id} onClick={() => onOpenChapter(chapter.id)}>
              <ListItemText primary={chapter.name} />
            </ListItemButton>
          ))}
        </List>
      ),
    },
  ].filter((tab): tab is { key: string; label: string; content: ReactElement } => tab !== false);

  const [activeTab, setActiveTab] = useState(0);

  if (tabs.length === 0) return null;

  // Guard against the active index pointing past the available tabs.
  const safeActiveTab = Math.min(activeTab, tabs.length - 1);

  return (
    <Box>
      <Tabs
        value={safeActiveTab}
        onChange={(_, newValue: number) => setActiveTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
        {tabs.map((tab) => (
          <Tab key={tab.key} label={tab.label} />
        ))}
      </Tabs>
      <Box sx={{ pt: 1 }}>{tabs[safeActiveTab]?.content}</Box>
    </Box>
  );
};
```

This drops the `QuoteIcon` import, the `NoteLinkedHighlight` type import, `PREVIEW_WORD_COUNT`, and `formatHighlightPreview` (all now unused), adds `Highlight`/`HighlightCard`/`Stack`, and keeps `List`/`ListItemButton`/`ListItemText` for the Chapters tab.

- [ ] **Step 2: Resolve full highlights in `NoteViewModal.tsx`**

In `frontend/src/pages/BookPage/Notes/NoteViewModal.tsx`:

(a) Add `Highlight` to the model type import and `useMemo` to the React import. The React import currently reads:

```tsx
import { useRef, useState } from 'react';
```

Change it to:

```tsx
import { useMemo, useRef, useState } from 'react';
```

And add the `Highlight` type import (place it with the other `@/api/generated/model` usage; there is no existing model import in this file, so add one near the top imports):

```tsx
import type { Highlight } from '@/api/generated/model';
```

(b) Replace the existing line:

```tsx
  const highlights = activeNote?.highlights ?? [];
```

with a resolution of full `Highlight` objects from the loaded book context:

```tsx
  // The note detail returns lightweight highlight summaries; resolve them to the
  // full Highlight objects already loaded on the book so we can render HighlightCard.
  const highlights = useMemo<Highlight[]>(() => {
    if (!activeNote?.highlights?.length) return [];
    const byId = new Map<number, Highlight>();
    for (const chapter of book.chapters) {
      for (const highlight of chapter.highlights) {
        byId.set(highlight.id, highlight);
      }
    }
    return activeNote.highlights
      .map((summary) => byId.get(summary.id))
      .filter((highlight): highlight is Highlight => highlight !== undefined);
  }, [book.chapters, activeNote?.highlights]);
```

Leave `chapters`, `highlightTags`, and the `<NoteLinkTabs ... highlights={highlights} ... />` usage as they are — `highlights` is now `Highlight[]`, matching the updated prop type. The `(highlights.length > 0 || chapters.length > 0)` render guard still holds.

- [ ] **Step 3: Type-check and lint**

Run:

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: no type errors, 0 lint warnings. If eslint flags an unused import in `NoteLinkTabs.tsx`, remove that specific import (Step 1 already accounts for the expected set).

- [ ] **Step 4: Manual check + commit**

Manual: run `npm run dev`, open a note that has linked highlights. The Highlights tab now shows `HighlightCard`s identical to the chapter detail dialog (label, tags, flashcard/note indicators, date). Clicking a card navigates to that highlight (note modal closes). A note with only linked chapters still shows just the Chapters tab, unchanged.

Commit both files together:

```bash
git add frontend/src/pages/BookPage/Notes/components/NoteLinkTabs.tsx frontend/src/pages/BookPage/Notes/NoteViewModal.tsx
git commit -m "Notes: reuse HighlightCard for linked highlights in note detail (#396 follow-up)"
```

---

## Self-Review Notes

- **Spec coverage:** frontend resolution from book context (Step 2), `NoteLinkTabs` uses `HighlightCard` with unchanged Chapters tab (Step 1), navigate-on-click preserved (`onOpenModal={onOpenHighlight}`), bookmark omitted, soft-deleted handling inherited (source is `activeNote.highlights`, already filtered; misses filtered out). All spec sections covered.
- **Placeholder scan:** no TBD/TODO; both files' complete final code is given.
- **Type consistency:** `NoteLinkTabs` `highlights` prop is `Highlight[]` in both the definition (Step 1) and the value passed from `NoteViewModal` (Step 2, the `useMemo` returns `Highlight[]`). `onOpenModal`/`onOpenHighlight` share signature `(highlightId: number) => void`.
- **Unused-symbol caution (`--max-warnings 0`):** Step 1 rewrites the whole file so no stale `QuoteIcon`/`formatHighlightPreview`/`NoteLinkedHighlight` remain; `List`/`ListItemButton`/`ListItemText` are retained because the Chapters tab still uses them.
