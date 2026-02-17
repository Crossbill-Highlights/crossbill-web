# Chapter Detail Dialog Design

## Problem

The app organizes content by type (highlights tab, flashcards tab, structure tab), but users need to see all content related to a specific chapter in one place. The StructureTab with inline prereading content feels heavy, and there's no way to navigate from a chapter's context to its highlights, flashcards, or prereading content without switching tabs and losing context.

## Solution

A **Chapter Detail Dialog** that serves as a chapter-centric hub, showing all content types for a single chapter in a scrollable dialog with collapsible sections. It opens from the StructureTab and preserves the user's position when closed.

## Design

### Dialog Structure

- Uses the existing `CommonDialog` component with `maxWidth="md"`
- **Title:** Chapter name
- **Header element:** Progress bar showing current chapter position (e.g., "3 / 18"), same component pattern as `HighlightViewModal`
- **Navigation:** Previous/next chapter arrows -- desktop: side arrows flanking content; mobile: bottom buttons. Same layout pattern as `HighlightViewModal`
- **Footer:** Close button
- Navigates through **leaf chapters only** (chapters without children), since parent chapters are structural containers without their own content
- Keyboard arrow navigation and swipe support, reusing `useHighlightNavigation` hook pattern

### Content Sections

The dialog body contains three collapsible sections, each with a clickable header to toggle expand/collapse:

#### 1. Prereading Summary

- **If generated:** Renders the existing `PrereadingContent` component (summary text + keypoints as markdown)
- **If not generated:** Shows a prompt with an AI generate button, gated by `AIFeature`
- **Default state:** Expanded if chapter is unread (reading position before chapter start), collapsed if read
- Prereading generation uses the existing mutation and invalidates the prereading query on success

#### 2. Highlights (count in header, e.g., "Highlights (7)")

- Shows the chapter's highlights using `HighlightCard` components (same as Highlights tab, may iterate to a more condensed variant later)
- Clicking a highlight opens the existing `HighlightViewModal` stacked on top of the chapter dialog (MUI handles dialog stacking natively)
- **Default state:** Expanded if chapter has highlights, collapsed if empty
- Shows "Highlights (0)" in header when empty

#### 3. Flashcards (count in header, e.g., "Flashcards (3)")

- Shows flashcards using `FlashcardCard` components, same UI pattern as in `HighlightViewModal` and `FlashcardsTab`
- Flashcards are derived from the chapter's highlights (same logic as `FlashcardsTab`)
- **Default state:** Expanded if chapter has flashcards, collapsed if empty
- Shows "Flashcards (0)" in header when empty

### StructureTab Changes

The StructureTab simplifies when the dialog handles chapter detail:

- **Leaf chapters** become clickable rows that open the Chapter Detail Dialog (instead of expandable accordions with inline prereading)
- **Parent chapters** remain expandable accordions that reveal children (unchanged behavior)
- Each leaf chapter row can show small indicator icons/counts for highlights and flashcards to preview what's inside
- The reading progress line continues to work as before
- The prereading content moves entirely out of the StructureTab and into the dialog

### Entry Points

**Initial scope:** StructureTab only. Clicking a leaf chapter row opens the dialog.

**Future expansion (not in initial scope):**
- Chapter header links in the Highlights tab's `SectionTitle` component
- Chapter header links in the Flashcards tab's `FlashcardChapterList`
- These would call the same dialog opener with a chapter ID

### Data Flow

**No new API endpoints required.** All data comes from existing sources:

- `BookDetails` (single fetch, already loaded by BookPage): chapters, highlights, flashcards, bookmarks
- Prereading query (`useGetBookPrereadingApiV1BooksBookIdPrereadingGet`): prereading content per chapter
- Prereading generation mutation (`useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost`): triggers AI generation

**State management:**
- `StructureTab` manages dialog state: `selectedChapterId` (number | null) and derived `open` boolean
- Clicking a leaf chapter sets the selected chapter ID and opens the dialog
- Closing the dialog clears the selection
- Scroll position is preserved by `CommonDialog`'s existing scroll lock/restore behavior

**Dialog stacking:**
- `HighlightViewModal` opens on top of `ChapterDetailDialog` when a highlight is clicked
- MUI's dialog system handles z-index and backdrop stacking
- `CommonDialog`'s scroll lock manages each dialog instance independently
- Closing the highlight modal returns to the chapter dialog

### Component Hierarchy

```
StructureTab
├── ReadingProgressLine
│   ├── ChapterAccordion (parent chapters - expandable, unchanged)
│   └── LeafChapterRow (clickable, opens dialog)
└── ChapterDetailDialog
    ├── CommonDialog (maxWidth="md")
    ├── ProgressBar (chapter index / total)
    ├── Navigation arrows (prev/next leaf chapter)
    ├── PrereadingSection (collapsible)
    │   └── PrereadingContent (existing component)
    ├── HighlightsSection (collapsible)
    │   ├── HighlightCard (existing component, per highlight)
    │   └── HighlightViewModal (opens on click, stacked)
    └── FlashcardsSection (collapsible)
        └── FlashcardCard (existing component, per flashcard)
```
