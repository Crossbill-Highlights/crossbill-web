# Book Stats Strip Design

## Overview

A stats strip displayed below the book info section (title, author, description, tags, edit button) on the BookPage. Shows reading progress, highlight count, flashcard count, and last read date in a single outlined card with vertical dividers.

## Component Structure

### `BookStatsStrip`
- **Location**: `frontend/src/pages/BookPage/BookTitle/BookStatsStrip.tsx`
- **Placement**: Below the existing book info grid in `BookTitle.tsx` (after the `<Box>` containing cover + info)
- **Container**: Single `Card variant="outlined"` with stat sections separated by `Divider orientation="vertical"`

### `StatItem` (internal to BookStatsStrip)
- Renders a single stat cell: large value, uppercase label, optional sublabel
- Not exported — just a helper within the file

## Data Sources

| Stat | Source | Calculation |
|------|--------|-------------|
| Progress % | `BookDetails.reading_position` / `BookDetails.end_position` | `Math.round((reading_position.index / end_position.index) * 100)`, 0% when no position |
| Highlights | `BookDetails.chapters` | Sum of all `chapter.highlights.length` |
| Flashcards | `BookDetails.book_flashcards` | `book_flashcards.length` |
| Started | `BookDetails.created_at` | Formatted with `formatDate()` |
| Last Read | Reading Sessions API | `useGetReadingSessions(bookId, { limit: 1 })` → first session's `start_time` |

## MUI Components

- `Card` with `variant="outlined"` — outer container
- `Divider` with `orientation="vertical"` — separators between stats
- `LinearProgress` with `variant="determinate"` — progress bar in first cell
- `Typography` — values and labels

## Responsive Behavior

- **Desktop (lg+)**: Horizontal row, 4 items with vertical dividers, flexShrink: 0
- **Mobile (xs-md)**: 2x2 grid with horizontal dividers between rows

## Layout in BookTitle.tsx

```
┌─────────────────────────────────────────────┐
│  Cover  │  Title                            │
│         │  Author                           │
│         │  Description                      │
│         │  [Edit]                           │
│         │  Tags                             │
├─────────────────────────────────────────────┤
│  ┌──────────┬──────────┬──────────┬────────┐│
│  │   31%    │    28    │    3     │ Jan 27 ││
│  │ PROGRESS │HIGHLIGHTS│FLASHCARDS│LAST READ│
│  │ ═══░░░░  │          │          │started… ││
│  └──────────┴──────────┴──────────┴────────┘│
└─────────────────────────────────────────────┘
```

The stats strip spans the full width below the grid, not inside the info column.

## Edge Cases

- No reading position → show 0% with "NOT STARTED" sublabel
- No reading sessions → show dash for last read date
- No flashcards/highlights → show 0
