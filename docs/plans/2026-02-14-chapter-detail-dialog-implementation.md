# Chapter Detail Dialog Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a chapter detail dialog that opens from the Structure tab and shows all chapter content (prereading, highlights, flashcards) in one view with chapter-to-chapter navigation.

**Architecture:** A `ChapterDetailDialog` component using `CommonDialog` with collapsible content sections. Reuses existing components (`PrereadingContent`, `HighlightCard`, `FlashcardListCard`) and navigation patterns (`useHighlightNavigation`, `ProgressBar`). State managed locally in `StructureTab` via `selectedChapterIndex`. No new API endpoints needed.

**Tech Stack:** React, MUI (Dialog, Accordion), motion/react (animations), TanStack Query (data), react-swipeable (navigation)

**Design doc:** `docs/plans/2026-02-14-chapter-detail-dialog-design.md`

---

## File Overview

All paths relative to `frontend/src/`.

**New files:**
- `pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx`
- `pages/BookPage/StructureTab/ChapterDetailDialog/CollapsibleSection.tsx`
- `pages/BookPage/StructureTab/ChapterDetailDialog/PrereadingSection.tsx`
- `pages/BookPage/StructureTab/ChapterDetailDialog/HighlightsSection.tsx`
- `pages/BookPage/StructureTab/ChapterDetailDialog/FlashcardsSection.tsx`

**Modified files:**
- `pages/BookPage/StructureTab/ChapterAccordion.tsx` (leaf rows become clickable with indicators, remove inline prereading)
- `pages/BookPage/StructureTab/StructureTab.tsx` (add dialog state, compute leaf chapters, wire dialog)

---

### Task 1: Create CollapsibleSection component

A reusable accordion section with a title, optional count badge, and expand/collapse toggle.

**Files:**
- Create: `pages/BookPage/StructureTab/ChapterDetailDialog/CollapsibleSection.tsx`

**Step 1: Create the component**

```tsx
// pages/BookPage/StructureTab/ChapterDetailDialog/CollapsibleSection.tsx
import { ExpandMoreIcon } from '@/theme/Icons.tsx';
import { Accordion, AccordionDetails, AccordionSummary, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface CollapsibleSectionProps {
  title: string;
  count?: number;
  defaultExpanded?: boolean;
  children: ReactNode;
}

export const CollapsibleSection = ({
  title,
  count,
  defaultExpanded = false,
  children,
}: CollapsibleSectionProps) => {
  const headerText = count !== undefined ? `${title} (${count})` : title;

  return (
    <Accordion
      defaultExpanded={defaultExpanded}
      sx={{
        boxShadow: 'none',
        '&:before': { display: 'none' },
        '&.Mui-expanded': { m: 0 },
        bgcolor: 'transparent',
        borderBottom: '1px solid',
        borderColor: 'divider',
        '&:last-of-type': { borderBottom: 'none', borderRadius: 0 },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          '&.Mui-expanded': { minHeight: 48 },
          '& .MuiAccordionSummary-content.Mui-expanded': { my: '12px' },
        }}
      >
        <Typography variant="body1" sx={{ fontWeight: 600, color: 'primary.main' }}>
          {headerText}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 0 }}>{children}</AccordionDetails>
    </Accordion>
  );
};
```

**Step 2: Verify it compiles**

Run: `cd frontend && npm run type-check`

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/CollapsibleSection.tsx
git commit -m "Add CollapsibleSection component for chapter detail dialog"
```

---

### Task 2: Create ChapterDetailDialog shell with navigation

The main dialog component with `CommonDialog`, `ProgressBar`, and prev/next chapter navigation. Content sections will be added in subsequent tasks.

**Files:**
- Create: `pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx`

**Step 1: Create the dialog component**

Reference patterns:
- Navigation layout: `pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx` (lines 196-263)
- Navigation hook: `pages/BookPage/HighlightsTab/HighlightViewModal/hooks/useHighlightNavigation.ts`
- Progress bar: `pages/BookPage/HighlightsTab/HighlightViewModal/components/ProgressBar.tsx`

```tsx
// pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx
import type {
  Bookmark,
  ChapterPrereadingResponse,
  ChapterWithHighlights,
  HighlightTagInBook,
  PositionResponse,
} from '@/api/generated/model';
import { FadeInOut } from '@/components/animations/FadeInOut.tsx';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { ProgressBar } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/components/ProgressBar.tsx';
import { useHighlightNavigation } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/hooks/useHighlightNavigation.ts';
import { ArrowBackIcon, ArrowForwardIcon } from '@/theme/Icons.tsx';
import { Box, Button, IconButton, Typography } from '@mui/material';

interface ChapterDetailDialogProps {
  open: boolean;
  onClose: () => void;
  chapter: ChapterWithHighlights;
  bookId: number;
  allLeafChapters: ChapterWithHighlights[];
  currentIndex: number;
  onNavigate: (newIndex: number) => void;
  prereadingByChapterId: Record<number, ChapterPrereadingResponse>;
  bookmarksByHighlightId: Record<number, Bookmark>;
  availableTags: HighlightTagInBook[];
  readingPosition?: PositionResponse | null;
}

export const ChapterDetailDialog = ({
  open,
  onClose,
  chapter,
  bookId,
  allLeafChapters,
  currentIndex,
  onNavigate,
  prereadingByChapterId,
  bookmarksByHighlightId,
  availableTags,
  readingPosition,
}: ChapterDetailDialogProps) => {
  const { hasNavigation, hasPrevious, hasNext, handlePrevious, handleNext, swipeHandlers } =
    useHighlightNavigation({
      open,
      currentIndex,
      totalCount: allLeafChapters.length,
      onNavigate,
    });

  const title = (
    <Typography
      variant="h6"
      component="span"
      sx={{
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        maxWidth: { xs: 'calc(100vw - 120px)', sm: 'calc(100vw - 200px)', md: '600px' },
        display: 'block',
      }}
    >
      {chapter.name}
    </Typography>
  );

  const renderContent = () => (
    <Box>
      <Typography variant="body2" color="text.secondary">
        Content sections will be added here.
      </Typography>
    </Box>
  );

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      title={title}
      headerElement={
        hasNavigation ? (
          <ProgressBar currentIndex={currentIndex} totalCount={allLeafChapters.length} />
        ) : undefined
      }
      footerActions={
        <Box sx={{ display: 'flex', justifyContent: 'end', width: '100%' }}>
          <Button onClick={onClose}>Close</Button>
        </Box>
      }
    >
      {/* Desktop Layout: Navigation buttons on sides */}
      <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'flex-start', gap: 2 }}>
        {hasNavigation && (
          <IconButton
            onClick={handlePrevious}
            disabled={!hasPrevious}
            sx={{ flexShrink: 0, visibility: hasPrevious ? 'visible' : 'hidden', mt: 1 }}
            aria-label="Previous chapter"
          >
            <ArrowBackIcon />
          </IconButton>
        )}

        <Box display="flex" flexDirection="column" gap={3} flex={1} {...swipeHandlers}>
          <FadeInOut ekey={chapter.id}>{renderContent()}</FadeInOut>
        </Box>

        {hasNavigation && (
          <IconButton
            onClick={handleNext}
            disabled={!hasNext}
            sx={{ flexShrink: 0, visibility: hasNext ? 'visible' : 'hidden', mt: 1 }}
            aria-label="Next chapter"
          >
            <ArrowForwardIcon />
          </IconButton>
        )}
      </Box>

      {/* Mobile Layout: Navigation buttons below */}
      <Box
        sx={{ display: { xs: 'flex', sm: 'none' }, flexDirection: 'column', gap: 3 }}
        {...swipeHandlers}
      >
        <FadeInOut ekey={chapter.id}>{renderContent()}</FadeInOut>

        {hasNavigation && (
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, pt: 1 }}>
            <Button
              onClick={handlePrevious}
              disabled={!hasPrevious}
              startIcon={<ArrowBackIcon />}
              variant="outlined"
              sx={{ flex: 1, maxWidth: '200px' }}
            >
              Previous
            </Button>
            <Button
              onClick={handleNext}
              disabled={!hasNext}
              endIcon={<ArrowForwardIcon />}
              variant="outlined"
              sx={{ flex: 1, maxWidth: '200px' }}
            >
              Next
            </Button>
          </Box>
        )}
      </Box>
    </CommonDialog>
  );
};
```

Note: `alignItems: 'flex-start'` instead of `'center'` (as used in HighlightViewModal) because the chapter dialog content is taller and the arrows should stick near the top rather than centering vertically.

**Step 2: Verify it compiles**

Run: `cd frontend && npm run type-check`

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx
git commit -m "Add ChapterDetailDialog shell with navigation"
```

---

### Task 3: Add PrereadingSection

The collapsible prereading section inside the dialog. Shows existing prereading content or a generate button.

**Files:**
- Create: `pages/BookPage/StructureTab/ChapterDetailDialog/PrereadingSection.tsx`
- Modify: `pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx`

**Step 1: Create PrereadingSection**

Reference:
- `pages/BookPage/StructureTab/PrereadingContent.tsx` (reused directly)
- `pages/BookPage/StructureTab/ChapterAccordion.tsx:133-148` (generate mutation pattern)

```tsx
// pages/BookPage/StructureTab/ChapterDetailDialog/PrereadingSection.tsx
import type { ChapterPrereadingResponse } from '@/api/generated/model';
import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
} from '@/api/generated/prereading/prereading';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { PrereadingContent } from '@/pages/BookPage/StructureTab/PrereadingContent.tsx';
import { AIIcon } from '@/theme/Icons.tsx';
import { Box, Button } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface PrereadingSectionProps {
  chapterId: number;
  bookId: number;
  prereading?: ChapterPrereadingResponse;
  defaultExpanded: boolean;
}

export const PrereadingSection = ({
  chapterId,
  bookId,
  prereading,
  defaultExpanded,
}: PrereadingSectionProps) => {
  const queryClient = useQueryClient();

  const { mutate: generate, isPending } =
    useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost({
      mutation: {
        onSuccess: () => {
          void queryClient.invalidateQueries({
            queryKey: getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey(bookId),
          });
        },
      },
    });

  const handleGenerate = () => {
    generate({ chapterId });
  };

  return (
    <CollapsibleSection title="Pre-reading" defaultExpanded={defaultExpanded}>
      {prereading || isPending ? (
        <PrereadingContent content={prereading} isGenerating={isPending} />
      ) : (
        <AIFeature
          fallback={
            <Box sx={{ py: 1, color: 'text.secondary', typography: 'body2' }}>
              No pre-reading overview available.
            </Box>
          }
        >
          <Box sx={{ py: 1 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<AIIcon />}
              onClick={handleGenerate}
            >
              Generate Pre-reading Overview
            </Button>
          </Box>
        </AIFeature>
      )}
    </CollapsibleSection>
  );
};
```

**Step 2: Add PrereadingSection to ChapterDetailDialog**

In `ChapterDetailDialog.tsx`, replace the placeholder `renderContent()` function with:

```tsx
import { PrereadingSection } from './PrereadingSection.tsx';

// Inside the component, replace renderContent:
const isChapterRead =
  readingPosition != null && chapter.start_position != null
    ? readingPosition.index >= chapter.start_position.index
    : false;

const prereading = prereadingByChapterId[chapter.id];

const renderContent = () => (
  <Box>
    <PrereadingSection
      chapterId={chapter.id}
      bookId={bookId}
      prereading={prereading}
      defaultExpanded={!isChapterRead}
    />
  </Box>
);
```

**Step 3: Verify it compiles**

Run: `cd frontend && npm run type-check`

**Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/PrereadingSection.tsx
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx
git commit -m "Add PrereadingSection to chapter detail dialog"
```

---

### Task 4: Add HighlightsSection with stacked HighlightViewModal

Shows the chapter's highlights and opens the existing `HighlightViewModal` on top of the chapter dialog when a highlight is clicked.

**Files:**
- Create: `pages/BookPage/StructureTab/ChapterDetailDialog/HighlightsSection.tsx`
- Modify: `pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx`

**Step 1: Create HighlightsSection**

Reference:
- `pages/BookPage/HighlightsTab/HighlightCard.tsx` (reused)
- `pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx` (stacked)

Uses local state for the stacked highlight modal (not URL-based like `useHighlightModal`, since we're already inside a dialog).

```tsx
// pages/BookPage/StructureTab/ChapterDetailDialog/HighlightsSection.tsx
import type { Bookmark, ChapterWithHighlights, HighlightTagInBook } from '@/api/generated/model';
import { HighlightCard } from '@/pages/BookPage/HighlightsTab/HighlightCard.tsx';
import { HighlightViewModal } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx';
import { Stack } from '@mui/material';
import { useCallback, useMemo, useState } from 'react';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface HighlightsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
  bookmarksByHighlightId: Record<number, Bookmark>;
  availableTags: HighlightTagInBook[];
}

export const HighlightsSection = ({
  chapter,
  bookId,
  bookmarksByHighlightId,
  availableTags,
}: HighlightsSectionProps) => {
  const [selectedHighlightIndex, setSelectedHighlightIndex] = useState<number | null>(null);

  const highlights = chapter.highlights;
  const count = highlights.length;

  const selectedHighlight = useMemo(
    () => (selectedHighlightIndex !== null ? highlights[selectedHighlightIndex] ?? null : null),
    [highlights, selectedHighlightIndex]
  );

  const handleOpenHighlight = useCallback(
    (highlightId: number) => {
      const index = highlights.findIndex((h) => h.id === highlightId);
      if (index !== -1) setSelectedHighlightIndex(index);
    },
    [highlights]
  );

  const handleCloseHighlight = useCallback(() => {
    setSelectedHighlightIndex(null);
  }, []);

  const handleNavigateHighlight = useCallback(
    (newIndex: number) => {
      setSelectedHighlightIndex(newIndex);
    },
    []
  );

  return (
    <>
      <CollapsibleSection title="Highlights" count={count} defaultExpanded={count > 0}>
        <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
          {highlights.map((highlight) => (
            <li key={highlight.id}>
              <HighlightCard
                highlight={highlight}
                bookmark={bookmarksByHighlightId[highlight.id]}
                onOpenModal={handleOpenHighlight}
              />
            </li>
          ))}
        </Stack>
      </CollapsibleSection>

      {selectedHighlight && (
        <HighlightViewModal
          highlight={selectedHighlight}
          bookId={bookId}
          open={true}
          onClose={handleCloseHighlight}
          availableTags={availableTags}
          bookmarksByHighlightId={bookmarksByHighlightId}
          allHighlights={highlights}
          currentIndex={selectedHighlightIndex ?? 0}
          onNavigate={handleNavigateHighlight}
        />
      )}
    </>
  );
};
```

**Step 2: Add HighlightsSection to ChapterDetailDialog**

In `ChapterDetailDialog.tsx`, add to the `renderContent()` function after PrereadingSection:

```tsx
import { HighlightsSection } from './HighlightsSection.tsx';

// Inside renderContent, after PrereadingSection:
<HighlightsSection
  chapter={chapter}
  bookId={bookId}
  bookmarksByHighlightId={bookmarksByHighlightId}
  availableTags={availableTags}
/>
```

**Step 3: Verify it compiles**

Run: `cd frontend && npm run type-check`

**Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/HighlightsSection.tsx
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx
git commit -m "Add HighlightsSection with stacked HighlightViewModal"
```

---

### Task 5: Add FlashcardsSection

Shows the chapter's flashcards with edit/delete support using existing `FlashcardListCard` and `FlashcardEditDialog`.

**Files:**
- Create: `pages/BookPage/StructureTab/ChapterDetailDialog/FlashcardsSection.tsx`
- Modify: `pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx`

**Step 1: Create FlashcardsSection**

Reference:
- `pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx` (pattern for rendering flashcard list)
- `pages/BookPage/FlashcardsTab/FlashcardListCard.tsx` (reused for edit/delete actions)
- `pages/BookPage/FlashcardsTab/FlashcardEditDialog.tsx` (reused for editing)
- `pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx:7-12` (`FlashcardWithContext` type)

```tsx
// pages/BookPage/StructureTab/ChapterDetailDialog/FlashcardsSection.tsx
import type { ChapterWithHighlights } from '@/api/generated/model';
import type { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { FlashcardEditDialog } from '@/pages/BookPage/FlashcardsTab/FlashcardEditDialog.tsx';
import { FlashcardListCard } from '@/pages/BookPage/FlashcardsTab/FlashcardListCard.tsx';
import { Stack } from '@mui/material';
import { flatMap } from 'lodash';
import { useCallback, useMemo, useState } from 'react';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface FlashcardsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
}

export const FlashcardsSection = ({ chapter, bookId }: FlashcardsSectionProps) => {
  const [editingFlashcard, setEditingFlashcard] = useState<FlashcardWithContext | null>(null);

  const flashcardsWithContext = useMemo(
    (): FlashcardWithContext[] =>
      flatMap(chapter.highlights, (highlight) =>
        highlight.flashcards.map((flashcard) => ({
          ...flashcard,
          highlight,
          chapterName: chapter.name,
          chapterId: chapter.id,
          highlightTags: highlight.highlight_tags,
        }))
      ),
    [chapter]
  );

  const count = flashcardsWithContext.length;

  const handleEditFlashcard = useCallback((flashcard: FlashcardWithContext) => {
    setEditingFlashcard(flashcard);
  }, []);

  const handleCloseEdit = useCallback(() => {
    setEditingFlashcard(null);
  }, []);

  return (
    <>
      <CollapsibleSection title="Flashcards" count={count} defaultExpanded={count > 0}>
        <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
          {flashcardsWithContext.map((flashcard) => (
            <li key={flashcard.id}>
              <FlashcardListCard
                flashcard={flashcard}
                bookId={bookId}
                onEdit={() => handleEditFlashcard(flashcard)}
                showSourceHighlight={false}
              />
            </li>
          ))}
        </Stack>
      </CollapsibleSection>

      {editingFlashcard && (
        <FlashcardEditDialog
          flashcard={editingFlashcard}
          bookId={bookId}
          open={true}
          onClose={handleCloseEdit}
        />
      )}
    </>
  );
};
```

Note: `showSourceHighlight={false}` because we're already in the chapter context -- showing source highlights would be redundant.

**Step 2: Add FlashcardsSection to ChapterDetailDialog**

In `ChapterDetailDialog.tsx`, add to `renderContent()` after HighlightsSection:

```tsx
import { FlashcardsSection } from './FlashcardsSection.tsx';

// Inside renderContent, after HighlightsSection:
<FlashcardsSection chapter={chapter} bookId={bookId} />
```

The final `renderContent` function should now be:

```tsx
const renderContent = () => (
  <Box>
    <PrereadingSection
      chapterId={chapter.id}
      bookId={bookId}
      prereading={prereading}
      defaultExpanded={!isChapterRead}
    />
    <HighlightsSection
      chapter={chapter}
      bookId={bookId}
      bookmarksByHighlightId={bookmarksByHighlightId}
      availableTags={availableTags}
    />
    <FlashcardsSection chapter={chapter} bookId={bookId} />
  </Box>
);
```

**Step 3: Verify it compiles**

Run: `cd frontend && npm run type-check`

**Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/FlashcardsSection.tsx
git add frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx
git commit -m "Add FlashcardsSection with edit dialog support"
```

---

### Task 6: Update ChapterAccordion

Leaf chapters become clickable rows that open the dialog. They show indicator counts for highlights and flashcards. Inline prereading display is removed.

**Files:**
- Modify: `pages/BookPage/StructureTab/ChapterAccordion.tsx`

**Step 1: Modify ChapterAccordion**

Changes:
1. Add `onChapterClick` prop (threaded through recursive children)
2. Replace `LeafChapterRow` -- make it clickable (entire row), add highlight/flashcard count indicators, remove AI generate button
3. Remove the leaf-with-prereading accordion case (prereading is now in the dialog)
4. All leaf chapters render as the new clickable `LeafChapterRow`

Reference the current file: `pages/BookPage/StructureTab/ChapterAccordion.tsx`

The updated `ChapterAccordionProps` interface adds:
```tsx
onChapterClick?: (chapterId: number) => void;
```

The updated `LeafChapterRow` becomes:
```tsx
import { FlashcardsIcon, HighlightsIcon } from '@/theme/Icons.tsx';
import { Box, ButtonBase, Typography } from '@mui/material';
import { flatMap, sumBy } from 'lodash';

const LeafChapterRow = ({
  chapter,
  depth,
  onClick,
}: {
  chapter: ChapterWithHighlights;
  depth: number;
  onClick?: () => void;
}) => {
  const highlightCount = chapter.highlights.length;
  const flashcardCount = sumBy(chapter.highlights, (h) => h.flashcards.length);

  return (
    <ButtonBase
      onClick={onClick}
      sx={(theme) => ({
        ml: theme.spacing(depth * 2),
        borderBottom: '1px solid',
        borderColor: 'divider',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: theme.spacing(1),
        px: theme.spacing(2),
        minHeight: 48,
        width: '100%',
        textAlign: 'left',
        '&:last-of-type': {
          borderBottom: depth > 0 ? 'none' : '1px solid',
          borderColor: 'divider',
        },
      })}
    >
      <Typography variant="body1" sx={{ fontWeight: 600 }}>
        {chapter.name}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, color: 'text.secondary' }}>
        {highlightCount > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <HighlightsIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption">{highlightCount}</Typography>
          </Box>
        )}
        {flashcardCount > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <FlashcardsIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption">{flashcardCount}</Typography>
          </Box>
        )}
      </Box>
    </ButtonBase>
  );
};
```

The `ChapterAccordion` component simplifies:
- Remove the `prereading`, `isPending`, `generate` logic (no longer needed here)
- Remove the `prereadingByChapterId` prop
- All leaf chapters use the new `LeafChapterRow` with `onClick` calling `onChapterClick?.(chapter.id)`
- Non-leaf chapters remain as `ExpandableChapter` with recursive children, passing `onChapterClick` through

**Step 2: Verify it compiles**

Run: `cd frontend && npm run type-check`

Note: `StructureTab.tsx` will have errors at this point because it still passes `prereadingByChapterId` to `ChapterAccordion`. This will be fixed in Task 7.

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/ChapterAccordion.tsx
git commit -m "Simplify ChapterAccordion: clickable leaf rows with indicators"
```

---

### Task 7: Wire everything together in StructureTab

Add dialog state management, compute leaf chapters, pass all required data to `ChapterDetailDialog`, and update `ChapterAccordion` usage.

**Files:**
- Modify: `pages/BookPage/StructureTab/StructureTab.tsx`

**Step 1: Update StructureTab**

Changes:
1. Add `selectedChapterIndex` state (number | null)
2. Compute `leafChapters` list (flat, document order, depth-first traversal)
3. Compute `bookmarksByHighlightId` from `book.bookmarks`
4. Handle `onChapterClick` -- find the chapter's index in `leafChapters` and set it
5. Render `ChapterDetailDialog`
6. Remove `prereadingByChapterId` prop from `ChapterAccordion` (it moved to the dialog level)

Reference the current file: `pages/BookPage/StructureTab/StructureTab.tsx`

Key additions:

```tsx
import { keyBy } from 'lodash';
import { useCallback, useState } from 'react';
import { ChapterDetailDialog } from './ChapterDetailDialog/ChapterDetailDialog.tsx';

// Inside the component:

// Compute leaf chapters in document order (depth-first)
const leafChapters = useMemo(() => {
  const result: ChapterWithHighlights[] = [];
  const collectLeaves = (parentId: number | null) => {
    const children = childrenByParentId.get(parentId) ?? [];
    for (const ch of children) {
      const hasChildren = (childrenByParentId.get(ch.id) ?? []).length > 0;
      if (hasChildren) {
        collectLeaves(ch.id);
      } else {
        result.push(ch);
      }
    }
  };
  collectLeaves(null);
  return result;
}, [childrenByParentId]);

// Dialog state
const [selectedChapterIndex, setSelectedChapterIndex] = useState<number | null>(null);

const selectedChapter = useMemo(
  () => (selectedChapterIndex !== null ? leafChapters[selectedChapterIndex] ?? null : null),
  [leafChapters, selectedChapterIndex]
);

const handleChapterClick = useCallback(
  (chapterId: number) => {
    const index = leafChapters.findIndex((ch) => ch.id === chapterId);
    if (index !== -1) setSelectedChapterIndex(index);
  },
  [leafChapters]
);

const handleDialogClose = useCallback(() => {
  setSelectedChapterIndex(null);
}, []);

const handleDialogNavigate = useCallback((newIndex: number) => {
  setSelectedChapterIndex(newIndex);
}, []);

// Compute bookmarks map
const bookmarksByHighlightId = useMemo(
  () => keyBy(book.bookmarks, 'highlight_id'),
  [book.bookmarks]
);
```

Update `ChapterAccordion` usage:
- Remove `prereadingByChapterId` prop
- Add `onChapterClick={handleChapterClick}` prop

Add `ChapterDetailDialog` render after the content:

```tsx
{selectedChapter && (
  <ChapterDetailDialog
    open={true}
    onClose={handleDialogClose}
    chapter={selectedChapter}
    bookId={book.id}
    allLeafChapters={leafChapters}
    currentIndex={selectedChapterIndex ?? 0}
    onNavigate={handleDialogNavigate}
    prereadingByChapterId={prereadingByChapterId}
    bookmarksByHighlightId={bookmarksByHighlightId}
    availableTags={book.highlight_tags}
    readingPosition={book.reading_position}
  />
)}
```

**Step 2: Verify it compiles**

Run: `cd frontend && npm run type-check`

**Step 3: Run lint and format**

Run: `cd frontend && npm run lint:fix && npm run format`

**Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/StructureTab.tsx
git commit -m "Wire ChapterDetailDialog into StructureTab"
```

---

### Task 8: Final verification and cleanup

Run full type-check and lint to verify everything works together.

**Step 1: Type-check**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 2: Lint**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Fix any issues found**

If there are type or lint errors, fix them.

**Step 4: Final commit if any fixes were needed**

```bash
git add -u
git commit -m "Fix type-check and lint issues"
```
