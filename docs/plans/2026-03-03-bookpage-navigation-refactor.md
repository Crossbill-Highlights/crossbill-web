# BookPage Navigation Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor BookPage from tab-based navigation to a layout route with nested routes, desktop left-column nav, mobile bottom nav bar, and tabbed filter drawer.

**Architecture:** TanStack Router layout route (`book.$bookId.tsx`) renders the book header, desktop nav sidebar, and Outlet. Child routes (`/structure`, `/highlights`, `/flashcards`, `/sessions`) render their own content and inject sidebar widgets via React portals into slots provided by the layout context.

**Tech Stack:** TanStack Router v1 (file-based routing), React 18 (portals, context), MUI v6 (BottomNavigation, Drawer, Tabs), React Query (data fetching)

**Design doc:** `docs/plans/2026-03-03-bookpage-navigation-refactor-design.md`

---

## Key Architecture Decisions

### Portal-Based Sidebar Injection
The layout renders a left column with nav links + an empty div slot. Child routes use `createPortal()` to inject additional widgets (tags, labels) into that slot. The layout exposes the slot element via `BookPageContext`.

### Content-Area Right Sidebar
The right sidebar is NOT managed by the layout. Child routes that need one (Highlights, Flashcards) render their own internal two-column grid within the Outlet content area. Views without right sidebars (Structure, Sessions) render single-column, naturally expanding to fill available space.

### Desktop Layout Grid
```
Layout:  280px | 1fr (flexible)
         ┌─────┬──────────────────────────────────┐
         │ Nav │  <Outlet />                       │
         │ --- │  (child controls internal layout) │
         │ [portal slot]                           │
         └─────┴──────────────────────────────────┘
```

---

## Task 1: Create BookPageContext

**Files:**
- Create: `frontend/src/pages/BookPage/BookPageContext.tsx`

**Step 1: Create the context file**

```tsx
import type { BookDetails } from '@/api/generated/model';
import { createContext, useContext } from 'react';

interface BookPageContextValue {
  book: BookDetails;
  isDesktop: boolean;
  leftSidebarEl: HTMLDivElement | null;
}

const BookPageContext = createContext<BookPageContextValue | null>(null);

export const BookPageProvider = BookPageContext.Provider;

// eslint-disable-next-line react-refresh/only-export-components
export const useBookPage = (): BookPageContextValue => {
  const context = useContext(BookPageContext);
  if (!context) {
    throw new Error('useBookPage must be used within a BookPageProvider');
  }
  return context;
};
```

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/BookPageContext.tsx
git commit -m "feat: add BookPageContext for shared book data and sidebar slots"
```

---

## Task 2: Create DesktopNavLinks Component

**Files:**
- Create: `frontend/src/pages/BookPage/navigation/DesktopNavLinks.tsx`
- Reference: `frontend/src/theme/Icons.tsx` (for existing icons)

**Step 1: Create the component**

```tsx
import {
  ChapterListIcon,
  FlashcardsIcon,
  HighlightsIcon,
  ReadingSessionIcon,
} from '@/theme/Icons.tsx';
import { Box, List, ListItemButton, ListItemIcon, ListItemText } from '@mui/material';
import { Link, useMatchRoute } from '@tanstack/react-router';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/book/$bookId/structure', label: 'Structure', icon: <ChapterListIcon /> },
  { to: '/book/$bookId/highlights', label: 'Highlights', icon: <HighlightsIcon /> },
  { to: '/book/$bookId/flashcards', label: 'Flashcards', icon: <FlashcardsIcon /> },
  { to: '/book/$bookId/sessions', label: 'Sessions', icon: <ReadingSessionIcon /> },
];

interface DesktopNavLinksProps {
  bookId: string;
}

export const DesktopNavLinks = ({ bookId }: DesktopNavLinksProps) => {
  const matchRoute = useMatchRoute();

  return (
    <Box sx={{ mb: 3 }}>
      <List disablePadding>
        {NAV_ITEMS.map((item) => {
          const isActive = !!matchRoute({ to: item.to, params: { bookId } });

          return (
            <ListItemButton
              key={item.to}
              component={Link}
              to={item.to}
              params={{ bookId }}
              selected={isActive}
              sx={{
                borderRadius: 1,
                mb: 0.5,
                py: 1,
                '&.Mui-selected': {
                  backgroundColor: 'action.selected',
                  '&:hover': {
                    backgroundColor: 'action.selected',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: isActive ? 'primary.main' : 'text.secondary' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  variant: 'body2',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'primary.main' : 'text.primary',
                }}
              />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );
};
```

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/navigation/DesktopNavLinks.tsx
git commit -m "feat: add DesktopNavLinks component for left sidebar navigation"
```

---

## Task 3: Create MobileBottomNav Component

**Files:**
- Create: `frontend/src/pages/BookPage/navigation/MobileBottomNav.tsx`

**Step 1: Create the component**

```tsx
import {
  ChapterListIcon,
  FlashcardsIcon,
  HighlightsIcon,
  ReadingSessionIcon,
} from '@/theme/Icons.tsx';
import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { useNavigate, useParams, useRouterState } from '@tanstack/react-router';

const getActiveTab = (pathname: string): string => {
  if (pathname.includes('/highlights')) return 'highlights';
  if (pathname.includes('/flashcards')) return 'flashcards';
  if (pathname.includes('/sessions')) return 'sessions';
  return 'structure';
};

export const MobileBottomNav = () => {
  const { bookId } = useParams({ strict: false });
  const { location } = useRouterState();
  const navigate = useNavigate();

  const activeTab = getActiveTab(location.pathname);

  const handleChange = (_event: React.SyntheticEvent, newValue: string) => {
    void navigate({
      to: `/book/$bookId/${newValue}`,
      params: { bookId: bookId! },
      replace: true,
    });
  };

  return (
    <Paper
      elevation={3}
      sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1100 }}
    >
      <BottomNavigation value={activeTab} onChange={handleChange} showLabels>
        <BottomNavigationAction
          value="structure"
          label="Structure"
          icon={<ChapterListIcon />}
        />
        <BottomNavigationAction
          value="highlights"
          label="Highlights"
          icon={<HighlightsIcon />}
        />
        <BottomNavigationAction
          value="flashcards"
          label="Flashcards"
          icon={<FlashcardsIcon />}
        />
        <BottomNavigationAction
          value="sessions"
          label="Sessions"
          icon={<ReadingSessionIcon />}
        />
      </BottomNavigation>
    </Paper>
  );
};
```

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/navigation/MobileBottomNav.tsx
git commit -m "feat: add MobileBottomNav for mobile route navigation"
```

---

## Task 4: Create FilterDrawer Component

**Files:**
- Create: `frontend/src/pages/BookPage/navigation/FilterDrawer.tsx`

The FilterDrawer is a mobile bottom drawer with internal tabs (Chapters, Tags, Bookmarks). It replaces the old MobileNavigation's individual drawer system.

**Step 1: Create the component**

```tsx
import { CloseIcon } from '@/theme/Icons.tsx';
import { Box, Drawer, IconButton, Tab, Tabs } from '@mui/material';
import { type ReactNode, useState } from 'react';

export interface FilterTab {
  label: string;
  content: ReactNode;
}

interface FilterDrawerProps {
  open: boolean;
  onClose: () => void;
  tabs: FilterTab[];
}

export const FilterDrawer = ({ open, onClose, tabs }: FilterDrawerProps) => {
  const [activeTab, setActiveTab] = useState(0);

  // Reset to first tab when drawer closes
  const handleClose = () => {
    onClose();
    setActiveTab(0);
  };

  return (
    <Drawer anchor="bottom" open={open} onClose={handleClose}>
      <Box sx={{ p: 2, pb: 6, maxHeight: '80vh', overflow: 'auto' }}>
        {/* Drag handle */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
          <Box
            sx={{
              width: 40,
              height: 4,
              borderRadius: 2,
              bgcolor: 'grey.300',
            }}
          />
        </Box>

        {/* Close button */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
          <IconButton edge="end" onClick={handleClose} aria-label="close" size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="fullWidth"
          sx={{ mb: 2 }}
        >
          {tabs.map((tab, i) => (
            <Tab key={i} label={tab.label} />
          ))}
        </Tabs>

        {/* Tab content */}
        {tabs[activeTab]?.content}
      </Box>
    </Drawer>
  );
};
```

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/navigation/FilterDrawer.tsx
git commit -m "feat: add FilterDrawer with tabbed filter content for mobile"
```

---

## Task 5: Add ContentWithSidebar Layout Component

**Files:**
- Modify: `frontend/src/components/layout/Layouts.tsx`

Add a two-column layout for child routes that need a right sidebar within their content area.

**Step 1: Add the new styled component**

Add after the existing `ThreeColumnLayout`:

```tsx
export const ContentWithSidebar = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: '1fr 280px',
  gap: theme.spacing(4),
  alignItems: 'start',
}));
```

**Step 2: Commit**

```bash
git add frontend/src/components/layout/Layouts.tsx
git commit -m "feat: add ContentWithSidebar layout component"
```

---

## Task 6: Refactor BookPage.tsx into Layout Shell

**Files:**
- Modify: `frontend/src/pages/BookPage/BookPage.tsx`

This is the biggest change. BookPage becomes the layout shell that renders the book header, sidebar, and Outlet. All tab logic, BookTabs component, and callback handlers are removed.

**Step 1: Rewrite BookPage.tsx**

Replace the entire file content with:

```tsx
import {
  getGetRecentlyViewedBooksApiV1BooksRecentlyViewedGetQueryKey,
  useGetBookDetailsApiV1BooksBookIdGet,
} from '@/api/generated/books/books';
import { FadeInOut } from '@/components/animations/FadeInOut.tsx';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { ScrollToTopButton } from '@/components/buttons/ScrollToTopButton.tsx';
import { PageContainer } from '@/components/layout/Layouts.tsx';
import { queryClient } from '@/lib/queryClient';
import { BookPageProvider } from '@/pages/BookPage/BookPageContext.tsx';
import { BookTitle } from '@/pages/BookPage/BookTitle/BookTitle.tsx';
import { DesktopNavLinks } from '@/pages/BookPage/navigation/DesktopNavLinks.tsx';
import { MobileBottomNav } from '@/pages/BookPage/navigation/MobileBottomNav.tsx';
import { Alert, Box, useMediaQuery, useTheme } from '@mui/material';
import { Outlet, useParams } from '@tanstack/react-router';
import { useEffect, useState } from 'react';

export const BookPage = () => {
  const { bookId } = useParams({ strict: false });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BooksBookIdGet(
    Number(bookId)
  );

  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  const [leftSidebarEl, setLeftSidebarEl] = useState<HTMLDivElement | null>(null);

  // Update recently viewed on mount
  useEffect(() => {
    void queryClient.invalidateQueries({
      queryKey: getGetRecentlyViewedBooksApiV1BooksRecentlyViewedGetQueryKey(),
    });
  }, []);

  if (isLoading) {
    return (
      <PageContainer maxWidth="xl">
        <Spinner />
      </PageContainer>
    );
  }

  if (isError || !book) {
    return (
      <PageContainer maxWidth="xl">
        <Box sx={{ pt: 4 }}>
          <Alert severity="error">Failed to load book details. Please try again later.</Alert>
        </Box>
      </PageContainer>
    );
  }

  return (
    <BookPageProvider value={{ book, isDesktop, leftSidebarEl }}>
      <PageContainer maxWidth="xl">
        <ScrollToTopButton />
        <FadeInOut ekey={`book-${bookId}`}>
          {isDesktop ? (
            <>
              <BookTitle book={book} />
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '280px 1fr',
                  gap: 4,
                  alignItems: 'start',
                }}
              >
                <Box>
                  <DesktopNavLinks bookId={String(bookId)} />
                  <div ref={setLeftSidebarEl} />
                </Box>
                <Box>
                  <Outlet />
                </Box>
              </Box>
            </>
          ) : (
            <Box sx={{ maxWidth: '800px', mx: 'auto' }}>
              <BookTitle book={book} />
              <Outlet />
            </Box>
          )}
        </FadeInOut>
        {!isDesktop && <MobileBottomNav />}
      </PageContainer>
    </BookPageProvider>
  );
};
```

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/BookPage.tsx
git commit -m "refactor: convert BookPage into layout shell with sidebar and Outlet"
```

---

## Task 7: Create Route Files

**Files:**
- Modify: `frontend/src/routes/book.$bookId.tsx`
- Create: `frontend/src/routes/book.$bookId/index.tsx`
- Create: `frontend/src/routes/book.$bookId/structure.tsx`
- Create: `frontend/src/routes/book.$bookId/highlights.tsx`
- Create: `frontend/src/routes/book.$bookId/flashcards.tsx`
- Create: `frontend/src/routes/book.$bookId/sessions.tsx`

**Step 1: Update the layout route file**

Replace `frontend/src/routes/book.$bookId.tsx` with:

```tsx
import { BookPage } from '@/pages/BookPage/BookPage';
import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
  beforeLoad: ({ search, params }) => {
    // Redirect old tab-based URLs to new nested routes
    const tabParam = (search as Record<string, unknown>).tab as string | undefined;
    if (tabParam) {
      const tabRouteMap: Record<string, string> = {
        highlights: 'highlights',
        flashcards: 'flashcards',
        readingSessions: 'sessions',
        structure: 'structure',
      };
      const route = tabRouteMap[tabParam] || 'structure';
      throw redirect({
        to: `/book/$bookId/${route}`,
        params,
      });
    }
  },
});
```

**Step 2: Create the index redirect**

Create `frontend/src/routes/book.$bookId/index.tsx`:

```tsx
import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId/')({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: '/book/$bookId/structure',
      params,
    });
  },
});
```

**Step 3: Create structure route**

Create `frontend/src/routes/book.$bookId/structure.tsx`:

```tsx
import { StructureTab } from '@/pages/BookPage/StructureTab/StructureTab';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId/structure')({
  component: StructureTab,
});
```

**Step 4: Create highlights route**

Create `frontend/src/routes/book.$bookId/highlights.tsx`:

```tsx
import { HighlightsTab } from '@/pages/BookPage/HighlightsTab/HighlightsTab';
import { createFileRoute } from '@tanstack/react-router';

type HighlightsSearch = {
  search?: string;
  tagId?: number;
  labelId?: number;
  highlightId?: number;
};

export const Route = createFileRoute('/book/$bookId/highlights')({
  component: HighlightsTab,
  validateSearch: (search: Record<string, unknown>): HighlightsSearch => ({
    search: (search.search as string | undefined) || undefined,
    tagId: (search.tagId as number | undefined) || undefined,
    labelId: (search.labelId as number | undefined) || undefined,
    highlightId: (search.highlightId as number | undefined) || undefined,
  }),
});
```

**Step 5: Create flashcards route**

Create `frontend/src/routes/book.$bookId/flashcards.tsx`:

```tsx
import { FlashcardsTab } from '@/pages/BookPage/FlashcardsTab/FlashcardsTab';
import { createFileRoute } from '@tanstack/react-router';

type FlashcardsSearch = {
  search?: string;
  tagId?: number;
  chapterId?: number;
};

export const Route = createFileRoute('/book/$bookId/flashcards')({
  component: FlashcardsTab,
  validateSearch: (search: Record<string, unknown>): FlashcardsSearch => ({
    search: (search.search as string | undefined) || undefined,
    tagId: (search.tagId as number | undefined) || undefined,
    chapterId: (search.chapterId as number | undefined) || undefined,
  }),
});
```

**Step 6: Create sessions route**

Create `frontend/src/routes/book.$bookId/sessions.tsx`:

```tsx
import { ReadingSessionsTab } from '@/pages/BookPage/ReadingSessionsTab/ReadingSessionsTab';
import { createFileRoute } from '@tanstack/react-router';

type SessionsSearch = {
  sessionPage?: number;
};

export const Route = createFileRoute('/book/$bookId/sessions')({
  component: ReadingSessionsTab,
  validateSearch: (search: Record<string, unknown>): SessionsSearch => ({
    sessionPage: search.sessionPage ? Number(search.sessionPage) : undefined,
  }),
});
```

**Step 7: Regenerate route tree**

Run: `cd frontend && npx tsr generate`

This regenerates `routeTree.gen.ts` with the new nested route structure.

**Step 8: Commit**

```bash
git add frontend/src/routes/book.\$bookId.tsx frontend/src/routes/book.\$bookId/ frontend/src/routeTree.gen.ts
git commit -m "feat: create nested route structure for BookPage views"
```

---

## Task 8: Refactor StructureTab

**Files:**
- Modify: `frontend/src/pages/BookPage/StructureTab/StructureTab.tsx`

Changes:
- Remove `book` and `isDesktop` props, get from `useBookPage()` context
- Remove `ThreeColumnLayout` usage (layout handles left column, this view has no right sidebar)
- Desktop: render content directly (it fills the content area from layout grid)
- Mobile: render content (already wrapped by layout's mobile container)

**Step 1: Refactor the component**

Key changes to make:

1. Remove the `StructureTabProps` interface and props
2. Add `import { useBookPage } from '@/pages/BookPage/BookPageContext';`
3. At the top of the component: `const { book, isDesktop } = useBookPage();`
4. Remove `ThreeColumnLayout` import and usage
5. Desktop: render `content` directly (no wrapper grid needed — layout provides left column)
6. Mobile: render `content` directly (no wrapper needed — layout provides mobile container)

The component becomes:

```tsx
export const StructureTab = () => {
  const { book, isDesktop } = useBookPage();
  // ... rest of logic stays the same, but remove ThreeColumnLayout wrappers
  // Desktop: just render {content} directly
  // Mobile: just render {content} directly (remove maxWidth wrapper, layout handles it)

  return (
    <>
      {content}
      {selectedChapter && <ChapterDetailDialog ... />}
    </>
  );
};
```

Remove the `isDesktop` conditional rendering that wraps in ThreeColumnLayout or Box. The layout already handles the column structure. If a max-width is needed for readability on wide screens, keep a simple `maxWidth` wrapper.

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/StructureTab/StructureTab.tsx
git commit -m "refactor: StructureTab to use BookPageContext instead of props"
```

---

## Task 9: Refactor ReadingSessionsTab

**Files:**
- Modify: `frontend/src/pages/BookPage/ReadingSessionsTab/ReadingSessionsTab.tsx`

Changes:
- Remove `book` and `isDesktop` props, get from `useBookPage()` context
- Remove `ThreeColumnLayout` usage
- Update `useSearch` from path to use the sessions route path: `useSearch({ from: '/book/$bookId/sessions' })`
- Update `useNavigate` from path: `useNavigate({ from: '/book/$bookId/sessions' })`

**Step 1: Refactor the component**

1. Remove `ReadingSessionsTabProps` interface
2. Add `import { useBookPage } from '@/pages/BookPage/BookPageContext';`
3. Get `{ book, isDesktop }` from `useBookPage()`
4. Update `useSearch({ from: '/book/$bookId/sessions' })`
5. Update `useNavigate({ from: '/book/$bookId/sessions' })`
6. Remove `ThreeColumnLayout` wrappers — just render `content` directly
7. Remove mobile `maxWidth` wrapper (layout handles it)

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/ReadingSessionsTab/ReadingSessionsTab.tsx
git commit -m "refactor: ReadingSessionsTab to use BookPageContext and session route"
```

---

## Task 10: Refactor HighlightsTab

**Files:**
- Modify: `frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx`

This is the most complex refactor. Changes:
- Remove all props, get `book` and `isDesktop` from `useBookPage()` context
- Move search param handlers (handleSearch, handleTagClick, handleLabelClick, handleBookmarkClick, handleChapterClick) into this component
- Update `useSearch` and `useNavigate` to use `/book/$bookId/highlights` path
- Desktop: use portal to inject Tags + Labels into layout's left sidebar slot; render content + right sidebar using `ContentWithSidebar`
- Mobile: replace `MobileNavigation` with `FilterDrawer` + filter button next to search bar

**Step 1: Refactor the component**

Key structural changes:

```tsx
import { createPortal } from 'react-dom';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { ContentWithSidebar } from '@/components/layout/Layouts';
import { FilterDrawer, type FilterTab } from '../navigation/FilterDrawer';
import { FilterIcon } from '@/theme/Icons'; // or use MUI's TuneIcon / FilterListIcon

export const HighlightsTab = () => {
  const { book, isDesktop, leftSidebarEl } = useBookPage();

  // Search params from this route
  const { search: urlSearch, tagId: urlTagId, labelId: urlLabelId } = useSearch({
    from: '/book/$bookId/highlights',
  });
  const navigate = useNavigate({ from: '/book/$bookId/highlights' });

  // State
  const searchText = urlSearch || '';
  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(urlTagId);
  const [selectedLabelId, setSelectedLabelId] = useState<number | undefined>(urlLabelId);
  const [isReversed, setIsReversed] = useState(false);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);

  // Navigation callbacks (moved from BookPageContent)
  const handleSearch = useCallback((value: string) => {
    navigate({ search: (prev) => ({ ...prev, search: value || undefined }), replace: true });
  }, [navigate]);

  const handleTagClick = (newTagId: number | null) => {
    setSelectedTagId(newTagId || undefined);
    navigate({ search: (prev) => ({ ...prev, tagId: newTagId || undefined }), replace: true });
  };

  const handleLabelClick = (newLabelId: number | null) => {
    setSelectedLabelId(newLabelId || undefined);
    navigate({ search: (prev) => ({ ...prev, labelId: newLabelId || undefined }), replace: true });
  };

  const handleBookmarkClick = useCallback((highlightId: number) => {
    if (urlSearch) {
      navigate({ search: (prev) => ({ ...prev, search: undefined }), replace: true });
    }
    scrollToElementWithHighlight(`highlight-${highlightId}`, { behavior: 'smooth' });
  }, [navigate, urlSearch]);

  const handleChapterClick = useCallback((chapterId: number) => {
    if (urlSearch) {
      navigate({ search: (prev) => ({ ...prev, search: undefined }), replace: true });
    }
    scrollToElementWithHighlight(`chapter-${chapterId}`, { behavior: 'smooth', block: 'start' });
  }, [navigate, urlSearch]);

  // ... existing filtering/search logic stays the same ...

  // Mobile filter drawer tabs
  const filterTabs: FilterTab[] = useMemo(() => {
    const tabs: FilterTab[] = [
      {
        label: 'Chapters',
        content: (
          <ChapterNav chapters={navData.chapters} onChapterClick={(id) => { handleChapterClick(id); setFilterDrawerOpen(false); }} hideTitle countType="highlight" />
        ),
      },
      {
        label: 'Tags',
        content: (
          <Box>
            <HighlightTagsList tags={tags} tagGroups={book.highlight_tag_groups} bookId={book.id} selectedTag={selectedTagId} onTagClick={(id) => { handleTagClick(id); setFilterDrawerOpen(false); }} hideTitle />
            <Box sx={{ mt: 3 }}>
              <HighlightLabelsList bookId={book.id} selectedLabelId={selectedLabelId} onLabelClick={(id) => { handleLabelClick(id); setFilterDrawerOpen(false); }} />
            </Box>
          </Box>
        ),
      },
      {
        label: 'Bookmarks',
        content: (
          <BookmarkList bookmarks={book.bookmarks} allHighlights={allHighlights} onBookmarkClick={(id) => { handleBookmarkClick(id); setFilterDrawerOpen(false); }} hideTitle />
        ),
      },
    ];
    return tabs;
  }, [/* deps */]);

  return (
    <>
      {/* Desktop: portal left sidebar content */}
      {isDesktop && leftSidebarEl && createPortal(
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <HighlightTagsList
            tags={tags}
            tagGroups={book.highlight_tag_groups}
            bookId={book.id}
            selectedTag={selectedTagId}
            onTagClick={handleTagClick}
          />
          <HighlightLabelsList
            bookId={book.id}
            selectedLabelId={selectedLabelId}
            onLabelClick={handleLabelClick}
          />
        </Box>,
        leftSidebarEl
      )}

      {/* Search bar + filter button */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
        <Box sx={{ flexGrow: 1 }}>
          <SearchBar onSearch={handleSearch} placeholder="Search highlights..." initialValue={searchText} />
        </Box>
        <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
          <IconButton onClick={() => setIsReversed(!isReversed)} sx={{ color: isReversed ? 'primary.main' : 'text.secondary' }}>
            <SortIcon />
          </IconButton>
        </Tooltip>
        {!isDesktop && (
          <IconButton onClick={() => setFilterDrawerOpen(true)} aria-label="Open filters">
            <FilterListIcon />
          </IconButton>
        )}
      </Box>

      {/* Content */}
      {isDesktop ? (
        <ContentWithSidebar>
          <HighlightsList ... />
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <BookmarkList bookmarks={book.bookmarks} allHighlights={allHighlights} onBookmarkClick={handleBookmarkClick} />
            <ChapterNav chapters={navData.chapters} onChapterClick={handleChapterClick} countType="highlight" />
          </Box>
        </ContentWithSidebar>
      ) : (
        <>
          <HighlightsList ... />
          <FilterDrawer open={filterDrawerOpen} onClose={() => setFilterDrawerOpen(false)} tabs={filterTabs} />
        </>
      )}

      {/* Highlight modal */}
      {currentHighlight && <HighlightViewModal ... />}
    </>
  );
};
```

Remove:
- `HighlightsTabProps` interface
- `MobileHighlightsContent` sub-component
- `DesktopHighlightsContent` sub-component
- `MobileNavigation` import and usage
- `ThreeColumnLayout` import and usage

The component is simplified: search bar + sort/filter buttons at the top, then conditional desktop/mobile content rendering below.

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx
git commit -m "refactor: HighlightsTab to standalone route with context, portals, and FilterDrawer"
```

---

## Task 11: Refactor FlashcardsTab

**Files:**
- Modify: `frontend/src/pages/BookPage/FlashcardsTab/FlashcardsTab.tsx`

Same pattern as HighlightsTab:
- Remove all props, use `useBookPage()` context
- Move search param handlers into this component
- Update `useSearch` / `useNavigate` to `/book/$bookId/flashcards` path
- Desktop: portal Tags into left sidebar, render content + right sidebar (ChapterNav) using `ContentWithSidebar`
- Mobile: FilterDrawer with Chapters and Tags tabs (no Bookmarks for flashcards)

**Step 1: Refactor the component**

Follow the same pattern as Task 10 but for flashcards:

```tsx
export const FlashcardsTab = () => {
  const { book, isDesktop, leftSidebarEl } = useBookPage();
  const { search: urlSearch, tagId: urlTagId } = useSearch({ from: '/book/$bookId/flashcards' });
  const navigate = useNavigate({ from: '/book/$bookId/flashcards' });

  // ... existing flashcard logic ...

  // Move handleSearch, handleTagClick, handleChapterClick here

  // Filter drawer tabs: Chapters, Tags (no Bookmarks)
  const filterTabs: FilterTab[] = useMemo(() => [
    {
      label: 'Chapters',
      content: <ChapterNav chapters={navData.chapters} onChapterClick={(id) => { handleChapterClick(id); setFilterDrawerOpen(false); }} hideTitle countType="flashcard" />,
    },
    {
      label: 'Tags',
      content: <HighlightTagsList tags={navData.tags} tagGroups={book.highlight_tag_groups} bookId={book.id} selectedTag={selectedTagId} onTagClick={(id) => { handleTagClick(id); setFilterDrawerOpen(false); }} hideTitle hideEmptyGroups />,
    },
  ], [/* deps */]);

  return (
    <>
      {/* Desktop: portal Tags into left sidebar */}
      {isDesktop && leftSidebarEl && createPortal(
        <HighlightTagsList tags={navData.tags} tagGroups={book.highlight_tag_groups} bookId={book.id} selectedTag={selectedTagId} onTagClick={handleTagClick} hideEmptyGroups />,
        leftSidebarEl
      )}

      {/* Search + filter */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
        <Box sx={{ flexGrow: 1 }}>
          <SearchBar onSearch={handleSearch} placeholder="Search flashcards..." initialValue={searchText} />
        </Box>
        {/* sort + filter buttons */}
      </Box>

      {/* Content */}
      {isDesktop ? (
        <ContentWithSidebar>
          <FlashcardChapterList ... />
          <ChapterNav chapters={navData.chapters} onChapterClick={handleChapterClick} countType="flashcard" />
        </ContentWithSidebar>
      ) : (
        <>
          <FlashcardChapterList ... />
          <FilterDrawer open={filterDrawerOpen} onClose={() => setFilterDrawerOpen(false)} tabs={filterTabs} />
        </>
      )}

      {editingFlashcard && <FlashcardEditDialog ... />}
    </>
  );
};
```

Remove:
- `FlashcardsTabProps` interface
- `MobileFlashcardsContent` sub-component
- `DesktopFlashcardsContent` sub-component
- `MobileNavigation` import and usage
- `ThreeColumnLayout` import and usage

**Step 2: Commit**

```bash
git add frontend/src/pages/BookPage/FlashcardsTab/FlashcardsTab.tsx
git commit -m "refactor: FlashcardsTab to standalone route with context, portals, and FilterDrawer"
```

---

## Task 12: Clean Up Old Components

**Files:**
- Delete: `frontend/src/pages/BookPage/navigation/MobileNavigation.tsx`
- Verify: no remaining imports of `MobileNavigation` or `BookTabs`

**Step 1: Delete MobileNavigation.tsx**

Run: `rm frontend/src/pages/BookPage/navigation/MobileNavigation.tsx`

**Step 2: Search for stale imports**

Run: `grep -r "MobileNavigation" frontend/src/ --include="*.tsx" --include="*.ts"`
Run: `grep -r "BookTabs" frontend/src/ --include="*.tsx" --include="*.ts"`

Fix any remaining imports.

**Step 3: Check for unused `ThreeColumnLayout` imports**

Run: `grep -r "ThreeColumnLayout" frontend/src/ --include="*.tsx" --include="*.ts"`

If only `Layouts.tsx` defines it and nothing imports it, remove it from `Layouts.tsx`. If other components still use it, keep it.

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove MobileNavigation and clean up stale imports"
```

---

## Task 13: Verify and Fix

**Step 1: Regenerate route tree**

Run: `cd frontend && npx tsr generate`

Verify `routeTree.gen.ts` contains the new nested routes.

**Step 2: Type check**

Run: `cd frontend && npm run type-check`

Fix all TypeScript errors. Common issues to expect:
- `useSearch`/`useNavigate` `from` paths need updating in refactored components
- Missing imports for `createPortal` from `react-dom`
- Filter icon import (may need to add `FilterListIcon` to `Icons.tsx` or import from MUI)
- Route type mismatches in generated code

**Step 3: Lint and format**

Run: `cd frontend && npm run lint:fix && npm run format`

**Step 4: Final commit**

```bash
git add -A
git commit -m "fix: resolve type errors and lint issues from navigation refactor"
```

---

## Task 14: Manual Testing Checklist

Verify in browser:

- [ ] `/book/123` redirects to `/book/123/structure`
- [ ] `/book/123?tab=highlights` redirects to `/book/123/highlights`
- [ ] Desktop: left sidebar shows nav links on all views
- [ ] Desktop: clicking nav links navigates between views
- [ ] Desktop: active nav link is highlighted
- [ ] Desktop: Highlights view shows Tags + Labels in left sidebar (below nav)
- [ ] Desktop: Highlights view shows Bookmarks + ChapterNav in right sidebar
- [ ] Desktop: Flashcards view shows Tags in left sidebar
- [ ] Desktop: Structure view has no extra sidebars, content expands
- [ ] Desktop: Sessions view has no extra sidebars, content expands
- [ ] Mobile: bottom nav bar visible on all views
- [ ] Mobile: tapping bottom nav navigates between views
- [ ] Mobile: filter button opens FilterDrawer
- [ ] Mobile: FilterDrawer has correct tabs per view
- [ ] Mobile: selecting a filter in drawer closes it and applies filter
- [ ] Search bar works on Highlights and Flashcards views
- [ ] Tag filtering works
- [ ] Label filtering works (Highlights)
- [ ] Bookmark navigation works
- [ ] Chapter navigation works
- [ ] Highlight modal works
- [ ] Browser back/forward works across views
- [ ] Deep links work (e.g., `/book/123/highlights?tagId=5`)

---

## Notes for Implementation

### FilterListIcon
The filter button needs an icon. Check if `FilterListIcon` or similar exists in `@/theme/Icons.tsx`. If not, import from MUI: `import FilterListIcon from '@mui/icons-material/FilterList'` or add it to the project's Icons.tsx.

### useSearch `from` Paths
After the refactor, `useSearch` in each tab component must reference the correct child route path:
- HighlightsTab: `useSearch({ from: '/book/$bookId/highlights' })`
- FlashcardsTab: `useSearch({ from: '/book/$bookId/flashcards' })`
- ReadingSessionsTab: `useSearch({ from: '/book/$bookId/sessions' })`

### Portal Timing
The left sidebar portal uses a callback ref (`setLeftSidebarEl`) so the element is available after the first render. Child routes check `leftSidebarEl !== null` before calling `createPortal()`. This is a standard React pattern and works without issues.

### Mobile Bottom Padding
The fixed bottom nav may overlap content. Ensure `PageContainer`'s bottom margin (currently `theme.spacing(10)` = 80px) is sufficient. If not, increase it for mobile breakpoints.
