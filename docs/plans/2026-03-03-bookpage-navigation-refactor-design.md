# BookPage Navigation Refactor Design

**Date:** 2026-03-03

## Goal

Refactor the BookPage from a tab-based navigation system to a layout with:
- **Desktop:** Vertical navigation links in a persistent left column, with view-specific sidebar widgets
- **Mobile:** Fixed bottom navigation bar + tabbed filter drawer replacing the current MobileNavigation

## Route Structure

**Current:** Single route `/book/$bookId` with `?tab=` search params.

**New:** TanStack Router layout route + nested child routes.

```
routes/
  book.$bookId.tsx              → Layout route (header, nav, sidebar slots, Outlet)
  book.$bookId/
    index.tsx                   → Redirects to /book/$bookId/structure
    structure.tsx               → /book/$bookId/structure
    highlights.tsx              → /book/$bookId/highlights
    flashcards.tsx              → /book/$bookId/flashcards
    sessions.tsx                → /book/$bookId/sessions
```

Each child route defines its own `validateSearch` for view-specific search params:
- `highlights.tsx`: `search`, `tagId`, `labelId`, `highlightId`
- `flashcards.tsx`: `search`, `tagId`, `chapterId`
- `sessions.tsx`: `sessionPage`
- `structure.tsx`: none

## Desktop Layout

The layout route renders a grid with a persistent left column containing navigation links. Child routes control additional sidebar content via a context-based slot mechanism.

```
┌─────────────────────────────────────────────────┐
│  Book Header (title, cover, stats)              │
├────────────┬────────────────────┬───────────────┤
│ Nav Links  │                    │ Right Col     │
│ ────────── │                    │ (optional)    │
│ View-      │  Content (Outlet)  │               │
│ specific   │                    │               │
│ widgets    │                    │               │
└────────────┴────────────────────┴───────────────┘
```

**Left column** (always present, 280px):
- Navigation links: Structure, Highlights, Flashcards, Sessions (active state from current route)
- Below: view-specific widgets injected by the child route (e.g., Tags + Labels for Highlights)

**Right column** (optional per view, 280px):
- Present for Highlights (bookmarks, chapter nav) and Flashcards (chapter nav)
- Absent for Structure and Sessions — content area expands to fill the space

**Grid behavior:** When no right column is needed, the layout switches from 3-column to 2-column so the content area expands.

### Left Column Content Per View

| View | Left Column (below nav) | Right Column |
|------|------------------------|--------------|
| Highlights | Tags, Labels | Bookmarks, ChapterNav |
| Flashcards | Tags | ChapterNav |
| Structure | (none) | (none) |
| Sessions | (none) | (none) |

## Mobile Layout

```
┌──────────────────────────┐
│ Book Header              │
│ (title, cover, stats)    │
├──────────────────────────┤
│ Search bar  [filter btn] │  ← per-view, rendered by child route
├──────────────────────────┤
│                          │
│ Content (Outlet)         │
│                          │
├──────────────────────────┤
│ Structure│Highlights│... │  ← fixed bottom nav (from layout)
└──────────────────────────┘
```

**Bottom navigation bar** (rendered by layout, fixed position, all views):
- 4 icon+label buttons: Structure, Highlights, Flashcards, Sessions
- Navigates between nested routes
- Active state highlights current route

**Filter drawer** (rendered by child routes that need it):
- Opened by filter button (funnel icon) next to the search bar
- Single bottom drawer with internal tabs: Chapters, Tags, Bookmarks
- Available tabs depend on current view (e.g., Bookmarks only on Highlights)
- Reuses existing `ChapterNav`, `HighlightTagsList`, `BookmarkList` components

## Component Architecture

### New Components

- **`DesktopNavLinks`** — Vertical list of 4 navigation links with icons, active state from current route
- **`MobileBottomNav`** — Fixed bottom bar with 4 icon+label buttons, navigates between nested routes
- **`FilterDrawer`** — Mobile bottom drawer with tabbed filter content (Chapters, Tags, Bookmarks). Configurable per view
- **`BookPageContext`** — React context providing book data and sidebar slot setters

### Modified Components

- **`book.$bookId.tsx`** — Becomes layout route rendering header, nav, sidebar slots, and `<Outlet />`
- **`BookPage.tsx`** — Simplified to layout shell, loses tab switching logic
- **`HighlightsTab`** → Route component at `book.$bookId/highlights.tsx`, manages its own sidebars + filter drawer
- **`FlashcardsTab`** → Route component at `book.$bookId/flashcards.tsx`, same pattern
- **`ReadingSessionsTab`** → Route component at `book.$bookId/sessions.tsx`, no sidebars
- **`StructureTab`** → Route component at `book.$bookId/structure.tsx`, no sidebars

### Removed Components

- **`BookTabs`** — Replaced by `DesktopNavLinks` + `MobileBottomNav`
- **`MobileNavigation`** — Replaced by `MobileBottomNav` + `FilterDrawer`

### Unchanged Components

- `ChapterNav`, `BookmarkList`, `HighlightTagsList`, `HighlightLabelsList` — Reused as-is
- `BookTitle` / `BookHeader` — Reused, just moved to layout level

## Data Flow

### Book Data
- Layout route fetches `BookDetails` via existing API hook
- Provided to children via `BookPageContext`

### Sidebar Slot Mechanism
`BookPageContext` exposes:
```typescript
interface BookPageContextValue {
  book: BookDetails;
  isDesktop: boolean;
  setLeftSidebarContent: (content: ReactNode) => void;
  setRightSidebarContent: (content: ReactNode) => void;
}
```

Child routes call `setLeftSidebarContent` / `setRightSidebarContent` in a `useEffect` on mount to inject their sidebar widgets into the layout's columns.

### Search Params
Each child route defines its own `validateSearch` and manages its own search param callbacks (handleSearch, handleTagClick, etc.).

### Filter Drawer (Mobile)
Managed locally within each child route that renders it. The `FilterDrawer` component receives configuration (which tabs to show, callbacks) as props.

## File Changes Summary

### New Files
- `routes/book.$bookId/index.tsx`
- `routes/book.$bookId/structure.tsx`
- `routes/book.$bookId/highlights.tsx`
- `routes/book.$bookId/flashcards.tsx`
- `routes/book.$bookId/sessions.tsx`
- `pages/BookPage/DesktopNavLinks.tsx`
- `pages/BookPage/MobileBottomNav.tsx`
- `pages/BookPage/FilterDrawer.tsx`
- `context/BookPageContext.tsx`

### Modified Files
- `routes/book.$bookId.tsx` — layout route
- `pages/BookPage/BookPage.tsx` — simplified layout shell
- `pages/BookPage/HighlightsTab/HighlightsTab.tsx` — refactored to route component
- `pages/BookPage/FlashcardsTab/FlashcardsTab.tsx` — refactored to route component
- `pages/BookPage/ReadingSessionsTab/ReadingSessionsTab.tsx` — refactored to route component
- `pages/BookPage/StructureTab/StructureTab.tsx` — refactored to route component

### Removed
- `BookTabs` component (inside BookPage.tsx)
- `pages/BookPage/navigation/MobileNavigation.tsx`

### No Changes
- Navigation sub-components (`ChapterNav`, `BookmarkList`, `HighlightTagsList`, `HighlightLabelsList`)
- Backend / API
