# Book Stats Strip Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a stats strip below the book info section showing reading progress, highlights, flashcards, and last read date.

**Architecture:** A `BookStatsStrip` component using MUI `Card variant="outlined"` with vertical `Divider` separators. Progress calculated from `reading_position`/`end_position`. Last read date fetched via reading sessions API with `limit=1`. Responsive: horizontal row on desktop, 2x2 grid on mobile.

**Tech Stack:** React, MUI (Card, Divider, LinearProgress, Typography), React Query (generated hooks), Luxon (date formatting)

**Design doc:** `docs/plans/2026-03-04-book-stats-strip-design.md`

---

### Task 1: Create BookStatsStrip component

**Files:**
- Create: `frontend/src/pages/BookPage/BookTitle/BookStatsStrip.tsx`
- Modify: `frontend/src/pages/BookPage/BookTitle/BookTitle.tsx`

**Step 1: Create the component file**

Create `frontend/src/pages/BookPage/BookTitle/BookStatsStrip.tsx`:

```tsx
import type { BookDetails } from '@/api/generated/model';
import { useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet } from '@/api/generated/reading-sessions/reading-sessions';
import { formatDate } from '@/utils/date';
import {
  Box,
  Card,
  Divider,
  LinearProgress,
  Typography,
} from '@mui/material';

interface StatItemProps {
  value: string;
  label: string;
  sublabel?: string;
  progress?: number; // 0-100, only for progress stat
}

const StatItem = ({ value, label, sublabel, progress }: StatItemProps) => (
  <Box
    sx={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      py: 1.5,
      px: 2,
      minWidth: 0,
    }}
  >
    <Typography variant="h6" component="span" sx={{ fontWeight: 'bold' }}>
      {value}
    </Typography>
    <Typography
      variant="caption"
      sx={{
        color: 'text.secondary',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        fontSize: '0.7rem',
      }}
    >
      {label}
    </Typography>
    {progress !== undefined && (
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ width: '100%', mt: 0.5, borderRadius: 1 }}
      />
    )}
    {sublabel && (
      <Typography
        variant="caption"
        sx={{ color: 'text.disabled', fontSize: '0.65rem', mt: 0.25 }}
      >
        {sublabel}
      </Typography>
    )}
  </Box>
);

interface BookStatsStripProps {
  book: BookDetails;
}

export const BookStatsStrip = ({ book }: BookStatsStripProps) => {
  const { data: sessionsData } = useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet(
    book.id,
    { limit: 1 },
  );

  // Calculate progress percentage
  const progress =
    book.reading_position && book.end_position && book.end_position.index > 0
      ? Math.round((book.reading_position.index / book.end_position.index) * 100)
      : 0;

  // Count highlights across all chapters
  const highlightCount = book.chapters.reduce(
    (sum, chapter) => sum + chapter.highlights.length,
    0,
  );

  // Count flashcards
  const flashcardCount = book.book_flashcards?.length ?? 0;

  // Last read date from latest session
  const latestSession = sessionsData?.sessions?.[0];
  const lastReadDate = latestSession ? formatDate(latestSession.start_time) : '—';

  // Started date from book creation
  const startedDate = formatDate(book.created_at);

  return (
    <Card
      variant="outlined"
      sx={{
        display: 'flex',
        flexDirection: { xs: 'row', sm: 'row' },
        flexWrap: { xs: 'wrap', sm: 'nowrap' },
      }}
    >
      <Box
        sx={{
          flex: { xs: '1 1 50%', sm: '1 1 0' },
          minWidth: 0,
        }}
      >
        <StatItem
          value={`${progress}%`}
          label="Progress"
          progress={progress}
        />
      </Box>

      <Divider
        orientation="vertical"
        flexItem
        sx={{ display: { xs: 'none', sm: 'block' } }}
      />
      <Divider
        sx={{ display: { xs: 'block', sm: 'none' }, width: '0' }}
      />

      <Box sx={{ flex: { xs: '1 1 50%', sm: '1 1 0' }, minWidth: 0 }}>
        <StatItem value={String(highlightCount)} label="Highlights" />
      </Box>

      {/* Full-width divider between rows on mobile */}
      <Box
        sx={{
          display: { xs: 'block', sm: 'none' },
          flexBasis: '100%',
          height: 0,
        }}
      >
        <Divider />
      </Box>

      <Divider
        orientation="vertical"
        flexItem
        sx={{ display: { xs: 'none', sm: 'block' } }}
      />

      <Box sx={{ flex: { xs: '1 1 50%', sm: '1 1 0' }, minWidth: 0 }}>
        <StatItem value={String(flashcardCount)} label="Flashcards" />
      </Box>

      <Divider
        orientation="vertical"
        flexItem
        sx={{ display: { xs: 'none', sm: 'block' } }}
      />
      <Divider
        sx={{ display: { xs: 'block', sm: 'none' }, width: '0' }}
      />

      <Box sx={{ flex: { xs: '1 1 50%', sm: '1 1 0' }, minWidth: 0 }}>
        <StatItem
          value={lastReadDate}
          label="Last Read"
          sublabel={`started ${startedDate}`}
        />
      </Box>
    </Card>
  );
};
```

**Step 2: Integrate into BookTitle.tsx**

In `frontend/src/pages/BookPage/BookTitle/BookTitle.tsx`, add the import at the top:

```tsx
import { BookStatsStrip } from './BookStatsStrip.tsx';
```

Then add `<BookStatsStrip book={book} />` after the closing `</Box>` of the grid (line 188) and before the edit modal. It should sit between the grid and the `BookEditModal`:

```tsx
      </Box>

      {/* Stats Strip */}
      <BookStatsStrip book={book} />

      {/* Edit Modal */}
      <BookEditModal book={book} open={editModalOpen} onClose={() => setEditModalOpen(false)} />
    </>
```

**Step 3: Run type check and lint**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: No errors

**Step 4: Visual verification**

Open the app in the browser, navigate to a book page, and verify:
- Stats strip appears below the book info grid
- 4 stats displayed horizontally on desktop
- Progress bar shows correct percentage
- Highlight and flashcard counts match
- Last read date loads (may show "—" briefly while fetching)
- On narrow viewport, stats wrap to 2x2 grid

**Step 5: Commit**

```bash
git add frontend/src/pages/BookPage/BookTitle/BookStatsStrip.tsx frontend/src/pages/BookPage/BookTitle/BookTitle.tsx
git commit -m "feat: add book stats strip showing progress, highlights, flashcards, last read"
```

---

### Task 2: Polish responsive layout and edge cases

**Files:**
- Modify: `frontend/src/pages/BookPage/BookTitle/BookStatsStrip.tsx`

**Step 1: Test edge cases**

Verify behavior with:
- A book with no reading position (should show 0%)
- A book with no reading sessions (should show "—" for last read)
- A book with 0 highlights and 0 flashcards

**Step 2: Adjust styling if needed**

Based on visual testing, adjust:
- Spacing/padding values
- Typography sizes
- Divider visibility at breakpoints
- Progress bar color/height

**Step 3: Run type check and lint**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/BookTitle/BookStatsStrip.tsx
git commit -m "fix: polish stats strip responsive layout and edge cases"
```
