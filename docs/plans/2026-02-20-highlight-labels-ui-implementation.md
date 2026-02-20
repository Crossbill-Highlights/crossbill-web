# Highlight Labels UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add frontend UI to display highlight labels as colored dots/chips, allow editing label text and color via a popover, and enable filtering highlights by label in the sidebar.

**Architecture:** Three new components (LabelIndicator, LabelEditorPopover, HighlightLabelsList) integrated into existing HighlightCard, HighlightViewModal, and sidebar/mobile navigation. Uses existing Orval-generated API hooks for data fetching and mutations. Label filtering follows the same URL-synced state pattern as tag filtering.

**Tech Stack:** React, MUI, react-color (CirclePicker), TanStack Router (URL state), TanStack Query (data fetching via Orval hooks)

**Design doc:** `docs/plans/2026-02-20-highlight-labels-ui-design.md`

---

### Task 1: Install react-color

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install the package**

Run: `cd frontend && npm install react-color`

**Step 2: Install type definitions**

Run: `cd frontend && npm install --save-dev @types/react-color`

**Step 3: Verify installation**

Run: `cd frontend && npm run type-check`
Expected: PASS (no new type errors)

**Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add react-color dependency for label color picker"
```

---

### Task 2: Add PaletteIcon to Icons.tsx

**Files:**
- Modify: `frontend/src/theme/Icons.tsx`

**Step 1: Add the icon export**

Add to the imports in `frontend/src/theme/Icons.tsx`:

```typescript
import PaletteOutlined from '@mui/icons-material/PaletteOutlined';
```

Add to the exports:

```typescript
export const PaletteIcon = PaletteOutlined;
```

Place it in the Content section alongside other content icons (TagIcon, etc.).

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/theme/Icons.tsx
git commit -m "feat: add PaletteIcon for highlight labels section"
```

---

### Task 3: Create LabelIndicator component

**Files:**
- Create: `frontend/src/pages/BookPage/common/LabelIndicator.tsx`

**Step 1: Create the component**

```typescript
import type { HighlightLabel } from '@/api/generated/model';
import { Box, Chip } from '@mui/material';

interface LabelIndicatorProps {
  label: HighlightLabel | null | undefined;
  onClick?: (event: React.MouseEvent<HTMLElement>) => void;
  size?: 'small' | 'medium';
}

const getContrastColor = (hexColor: string): string => {
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? '#000000' : '#FFFFFF';
};

export const LabelIndicator = ({ label, onClick, size = 'small' }: LabelIndicatorProps) => {
  if (!label?.ui_color) {
    return null;
  }

  const isClickable = !!onClick;
  const dotSize = size === 'small' ? 10 : 14;

  if (label.text) {
    return (
      <Chip
        label={label.text}
        size="small"
        onClick={onClick}
        sx={{
          backgroundColor: label.ui_color,
          color: getContrastColor(label.ui_color),
          fontWeight: 500,
          fontSize: size === 'small' ? '0.7rem' : '0.8rem',
          height: size === 'small' ? 22 : 26,
          cursor: isClickable ? 'pointer' : 'default',
          '&:hover': isClickable
            ? { opacity: 0.85 }
            : {},
        }}
      />
    );
  }

  return (
    <Box
      onClick={onClick}
      sx={{
        width: dotSize,
        height: dotSize,
        borderRadius: '50%',
        backgroundColor: label.ui_color,
        flexShrink: 0,
        cursor: isClickable ? 'pointer' : 'default',
        transition: 'transform 0.15s',
        '&:hover': isClickable
          ? { transform: 'scale(1.3)' }
          : {},
      }}
    />
  );
};
```

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/common/LabelIndicator.tsx
git commit -m "feat: add LabelIndicator component for dot/chip display"
```

---

### Task 4: Add LabelIndicator to HighlightCard footer

**Files:**
- Modify: `frontend/src/pages/BookPage/HighlightsTab/HighlightCard.tsx`

**Step 1: Add the label indicator**

In the `Footer` component, add `LabelIndicator` between the metadata row and the `BookTagList`. The Footer currently has two `Box` children inside a flex column/row container. Insert the LabelIndicator before the BookTagList box.

Import `LabelIndicator`:
```typescript
import { LabelIndicator } from '@/pages/BookPage/common/LabelIndicator.tsx';
```

In the Footer's JSX, add a new Box containing LabelIndicator between the metadata Box and the BookTagList Box, only wrapping both in a flex row:

```tsx
<Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 4.5 }}>
  <LabelIndicator label={highlight.label} size="small" />
  <BookTagList tags={highlight.highlight_tags} />
</Box>
```

This replaces the existing standalone `<Box><BookTagList ... /></Box>`.

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/HighlightsTab/HighlightCard.tsx
git commit -m "feat: display label dot/chip in highlight card footer"
```

---

### Task 5: Add LabelIndicator to HighlightContent (modal metadata)

**Files:**
- Modify: `frontend/src/pages/BookPage/common/HighlightContent.tsx`

**Step 1: Add label indicator inline with metadata**

The `HighlightContent` component has a metadata Box at the bottom with DateIcon and a Typography showing date + page. Add `LabelIndicator` as the last child of this metadata Box.

Import:
```typescript
import { LabelIndicator } from '@/pages/BookPage/common/LabelIndicator.tsx';
```

Add props for onClick to support opening the editor:
```typescript
interface HighlightContentProps {
  highlight: Highlight;
  onLabelClick?: (event: React.MouseEvent<HTMLElement>) => void;
}
```

In the metadata Box (the one with `display: 'flex', gap: 2, alignItems: 'center', opacity: 0.8`), add after the Typography:

```tsx
<LabelIndicator label={highlight.label} onClick={onLabelClick} size="medium" />
```

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/common/HighlightContent.tsx
git commit -m "feat: display clickable label indicator in highlight modal metadata"
```

---

### Task 6: Create LabelEditorPopover component

**Files:**
- Create: `frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/components/LabelEditorPopover.tsx`

**Step 1: Create the component**

```typescript
import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  getGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGetQueryKey,
  useUpdateHighlightLabelApiV1HighlightLabelsStyleIdPatch,
} from '@/api/generated/highlight-labels/highlight-labels.ts';
import { Box, Popover, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { CirclePicker, type ColorResult } from 'react-color';

const LABEL_COLORS = [
  '#F59E0B', // Yellow (KOReader)
  '#F97316', // Orange (KOReader)
  '#EF4444', // Red (KOReader)
  '#EC4899', // Pink
  '#8B5CF6', // Purple (KOReader)
  '#6366F1', // Indigo
  '#3B82F6', // Blue (KOReader)
  '#06B6D4', // Cyan (KOReader)
  '#14B8A6', // Teal
  '#10B981', // Green (KOReader)
  '#84CC16', // Olive (KOReader)
  '#059669', // Emerald
  '#6B7280', // Gray (KOReader)
  '#475569', // Slate
];

interface LabelEditorPopoverProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
  styleId: number;
  currentLabel?: string | null;
  currentColor?: string | null;
  bookId: number;
}

export const LabelEditorPopover = ({
  anchorEl,
  open,
  onClose,
  styleId,
  currentLabel,
  currentColor,
  bookId,
}: LabelEditorPopoverProps) => {
  const queryClient = useQueryClient();
  const [labelText, setLabelText] = useState(currentLabel || '');

  useEffect(() => {
    setLabelText(currentLabel || '');
  }, [currentLabel, open]);

  const updateMutation = useUpdateHighlightLabelApiV1HighlightLabelsStyleIdPatch({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
        void queryClient.invalidateQueries({
          queryKey: getGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGetQueryKey(bookId),
        });
      },
      onError: (error: Error) => {
        console.error('Failed to update label:', error);
      },
    },
  });

  const handleLabelSubmit = () => {
    const trimmed = labelText.trim();
    if (trimmed !== (currentLabel || '')) {
      updateMutation.mutate({
        styleId,
        data: { label: trimmed || null },
      });
    }
  };

  const handleColorChange = (color: ColorResult) => {
    updateMutation.mutate({
      styleId,
      data: { ui_color: color.hex },
    });
  };

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={() => {
        handleLabelSubmit();
        onClose();
      }}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      transformOrigin={{ vertical: 'top', horizontal: 'left' }}
    >
      <Box sx={{ p: 2, width: 280 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Edit Label
        </Typography>
        <TextField
          value={labelText}
          onChange={(e) => setLabelText(e.target.value)}
          onBlur={handleLabelSubmit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              handleLabelSubmit();
            }
          }}
          placeholder="Label name..."
          size="small"
          fullWidth
          autoFocus
          sx={{ mb: 2 }}
        />
        <Typography variant="caption" sx={{ mb: 1, display: 'block', color: 'text.secondary' }}>
          Color
        </Typography>
        <CirclePicker
          color={currentColor || undefined}
          colors={LABEL_COLORS}
          onChangeComplete={handleColorChange}
          width="100%"
        />
      </Box>
    </Popover>
  );
};
```

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/components/LabelEditorPopover.tsx
git commit -m "feat: add LabelEditorPopover with text input and color picker"
```

---

### Task 7: Wire up LabelEditorPopover in HighlightViewModal

**Files:**
- Modify: `frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx`

**Step 1: Add popover state and pass onClick to HighlightContent**

Import `LabelEditorPopover`:
```typescript
import { LabelEditorPopover } from './components/LabelEditorPopover.tsx';
```

Add state for the popover anchor:
```typescript
const [labelAnchorEl, setLabelAnchorEl] = useState<HTMLElement | null>(null);
```

Create a handler:
```typescript
const handleLabelClick = (event: React.MouseEvent<HTMLElement>) => {
  if (highlight.label?.highlight_style_id) {
    setLabelAnchorEl(event.currentTarget);
  }
};
```

Pass `onLabelClick={handleLabelClick}` to `HighlightContent`.

Add the popover after `ConfirmationDialog`, only when highlight has a label with style_id:

```tsx
{highlight.label?.highlight_style_id && (
  <LabelEditorPopover
    anchorEl={labelAnchorEl}
    open={!!labelAnchorEl}
    onClose={() => setLabelAnchorEl(null)}
    styleId={highlight.label.highlight_style_id}
    currentLabel={highlight.label.text}
    currentColor={highlight.label.ui_color}
    bookId={bookId}
  />
)}
```

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx
git commit -m "feat: wire up label editor popover in highlight view modal"
```

---

### Task 8: Create HighlightLabelsList component

**Files:**
- Create: `frontend/src/pages/BookPage/navigation/HighlightLabelsList.tsx`

**Step 1: Create the component**

```typescript
import { useGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGet } from '@/api/generated/highlight-labels/highlight-labels.ts';
import type { HighlightLabelInBook } from '@/api/generated/model';
import { PaletteIcon } from '@/theme/Icons.tsx';
import { Box, Chip, Typography } from '@mui/material';

interface HighlightLabelsListProps {
  bookId: number;
  selectedLabelId?: number | null;
  onLabelClick: (labelId: number | null) => void;
  hideTitle?: boolean;
}

const getContrastColor = (hexColor: string): string => {
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? '#000000' : '#FFFFFF';
};

const getLabelDisplayText = (label: HighlightLabelInBook): string => {
  if (label.label) {
    return label.label;
  }
  const parts = [label.device_color, label.device_style].filter(Boolean);
  return parts.join(' / ') || 'Unlabeled';
};

export const HighlightLabelsList = ({
  bookId,
  selectedLabelId,
  onLabelClick,
  hideTitle,
}: HighlightLabelsListProps) => {
  const { data: labels } = useGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGet(bookId);

  if (!labels || labels.length < 2) {
    return null;
  }

  return (
    <Box>
      {!hideTitle && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mb: 2,
            pb: 1.5,
          }}
        >
          <PaletteIcon sx={{ fontSize: 18, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
            Labels
          </Typography>
        </Box>
      )}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
        {labels.map((label) => {
          const isSelected = selectedLabelId === label.id;
          const displayText = getLabelDisplayText(label);
          const bgColor = label.ui_color || '#6B7280';

          return (
            <Chip
              key={label.id}
              label={`${displayText} (${label.highlight_count})`}
              size="small"
              onClick={() => onLabelClick(isSelected ? null : label.id)}
              sx={{
                backgroundColor: isSelected ? bgColor : 'transparent',
                color: isSelected ? getContrastColor(bgColor) : 'text.primary',
                fontWeight: 500,
                border: '1px solid',
                borderColor: isSelected ? bgColor : 'divider',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                py: 0.25,
                px: 0.5,
                '&:hover': {
                  backgroundColor: isSelected ? bgColor : 'action.hover',
                  borderColor: isSelected ? bgColor : 'secondary.light',
                  transform: 'translateY(-1px)',
                },
                '&::before': {
                  content: '""',
                  display: 'inline-block',
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: bgColor,
                  marginRight: '6px',
                  flexShrink: 0,
                },
              }}
            />
          );
        })}
      </Box>
    </Box>
  );
};
```

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/navigation/HighlightLabelsList.tsx
git commit -m "feat: add HighlightLabelsList component for sidebar label filtering"
```

---

### Task 9: Add labelId URL param support

**Files:**
- Modify: `frontend/src/routes/book.$bookId.tsx`

**Step 1: Add labelId to BookPageSearch**

Add `labelId?: number` to the `BookPageSearch` type:

```typescript
type BookPageSearch = {
  search?: string;
  tagId?: number;
  labelId?: number;
  highlightId?: number;
  chapterId?: number;
  tab?: 'highlights' | 'flashcards' | 'readingSessions' | 'structure';
  sessionPage?: number;
};
```

Add validation in `validateSearch`:

```typescript
labelId: (search.labelId as number | undefined) || undefined,
```

**Step 2: Add onLabelClick handler in BookPage**

Modify: `frontend/src/pages/BookPage/BookPage.tsx`

Add a `handleLabelClick` callback in `BookPageContent` (alongside `handleTagClick`):

```typescript
const handleLabelClick = useCallback(
  (newLabelId: number | null) => {
    navigate({
      search: (prev) => ({
        ...prev,
        labelId: newLabelId || undefined,
      }),
      replace: true,
    });
  },
  [navigate]
);
```

Pass `onLabelClick={handleLabelClick}` as a new prop to `HighlightsTab`.

**Step 3: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 4: Commit**

```bash
git add frontend/src/routes/book.\$bookId.tsx frontend/src/pages/BookPage/BookPage.tsx
git commit -m "feat: add labelId URL param and onLabelClick handler"
```

---

### Task 10: Add label filtering to HighlightsTab

**Files:**
- Modify: `frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx`

**Step 1: Add onLabelClick prop and label state**

Add to `HighlightsTabProps`:
```typescript
onLabelClick: (labelId: number | null) => void;
```

Read `labelId` from URL alongside `tagId`:
```typescript
const { search: urlSearch, tagId: urlTagId, labelId: urlLabelId } = useSearch({ from: '/book/$bookId' });
```

Add local state:
```typescript
const [selectedLabelId, setSelectedLabelId] = useState<number | undefined>(urlLabelId);
```

Add useEffect sync:
```typescript
useEffect(() => {
  setSelectedLabelId(urlLabelId);
}, [urlLabelId]);
```

Add handler:
```typescript
const handleLabelClick = (newLabelId: number | null) => {
  setSelectedLabelId(newLabelId || undefined);
  onLabelClick(newLabelId);
};
```

**Step 2: Add filterChaptersByLabel function**

Add alongside `filterChaptersByTag`:

```typescript
function filterChaptersByLabel(
  selectedLabelId: number | undefined,
  chaptersWithHighlights: ChapterWithHighlights[]
) {
  if (!selectedLabelId) {
    return chaptersWithHighlights;
  }

  return chaptersWithHighlights
    .map((chapter) => ({
      ...chapter,
      highlights: chapter.highlights.filter(
        (highlight) => highlight.label?.highlight_style_id === selectedLabelId
      ),
    }))
    .filter((chapter) => chapter.highlights.length > 0);
}
```

**Step 3: Apply label filter in chapters pipeline**

In the `chapters` useMemo, chain `filterChaptersByLabel` after `filterChaptersByTag`:

```typescript
const result = filterChaptersByLabel(
  selectedLabelId,
  filterChaptersByTag(selectedTagId, toFilter)
).map((chapter) => ({
  ...
}));
```

Add `selectedLabelId` to the useMemo dependency array.

**Step 4: Update empty message**

Update the `emptyMessage` useMemo to account for label filtering:

```typescript
const emptyMessage = useMemo(() => {
  if (bookSearch.showSearchResults) {
    if (selectedTagId && selectedLabelId) return 'No highlights found matching your search with the selected tag and label.';
    if (selectedTagId) return 'No highlights found matching your search with the selected tag.';
    if (selectedLabelId) return 'No highlights found matching your search with the selected label.';
    return 'No highlights found matching your search.';
  }
  if (selectedTagId && selectedLabelId) return 'No highlights found with the selected tag and label.';
  if (selectedTagId) return 'No highlights found with the selected tag.';
  if (selectedLabelId) return 'No highlights found with the selected label.';
  return 'No chapters found for this book.';
}, [bookSearch.showSearchResults, selectedTagId, selectedLabelId]);
```

**Step 5: Pass label props to Desktop and Mobile components**

Pass `selectedLabelId` and `handleLabelClick` to `DesktopHighlightsContent` and `MobileNavigation`.

**Step 6: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 7: Commit**

```bash
git add frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx
git commit -m "feat: add label filtering logic to highlights tab"
```

---

### Task 11: Integrate HighlightLabelsList into desktop sidebar

**Files:**
- Modify: `frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx` (DesktopHighlightsContent)

**Step 1: Add props and render HighlightLabelsList**

Add to `DesktopHighlightsContentProps`:
```typescript
selectedLabelId: number | undefined;
onLabelClick: (labelId: number | null) => void;
```

Import `HighlightLabelsList`:
```typescript
import { HighlightLabelsList } from '../navigation/HighlightLabelsList.tsx';
```

In the left column of `ThreeColumnLayout`, wrap HighlightTagsList and HighlightLabelsList in a Box with flex column layout:

```tsx
<Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
  <HighlightTagsList
    tags={tags}
    tagGroups={book.highlight_tag_groups}
    bookId={book.id}
    selectedTag={selectedTagId}
    onTagClick={onTagClick}
  />
  <HighlightLabelsList
    bookId={book.id}
    selectedLabelId={selectedLabelId}
    onLabelClick={onLabelClick}
  />
</Box>
```

**Step 2: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx
git commit -m "feat: add highlight labels list to desktop sidebar"
```

---

### Task 12: Integrate HighlightLabelsList into mobile Tags drawer

**Files:**
- Modify: `frontend/src/pages/BookPage/navigation/MobileNavigation.tsx`

**Step 1: Add label props to TagsDrawerContent and MobileNavigation**

Add to `TagsDrawerContentProps`:
```typescript
selectedLabelId?: number | null;
onLabelClick: (labelId: number | null) => void;
bookId: number;
```

Wait - `book` already provides `book.id`. Let's use it.

Import `HighlightLabelsList`:
```typescript
import { HighlightLabelsList } from './HighlightLabelsList.tsx';
```

Add to `TagsDrawerContent`, after `HighlightTagsList`:
```tsx
<Box sx={{ mt: 3 }}>
  <HighlightLabelsList
    bookId={book.id}
    selectedLabelId={selectedLabelId}
    onLabelClick={onLabelClick}
    hideTitle={false}
  />
</Box>
```

The `onLabelClick` in the drawer should also close the drawer (same pattern as tags):
```typescript
onLabelClick={(data) => {
  onLabelClick(data);
  setDrawerState(false);
}}
```

Update `MobileNavigationProps` to include `selectedLabelId` and `onLabelClick`, and thread them through to `TagsDrawerContent`.

**Step 2: Thread label props from HighlightsTab to MobileNavigation**

In `HighlightsTab.tsx`, pass the new props to `MobileNavigation`:

```tsx
<MobileNavigation
  ...
  selectedLabelId={selectedLabelId}
  onLabelClick={handleLabelClick}
/>
```

**Step 3: Verify**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/navigation/MobileNavigation.tsx frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx
git commit -m "feat: add highlight labels to mobile tags drawer"
```

---

### Task 13: Final verification and cleanup

**Step 1: Run type-check**

Run: `cd frontend && npm run type-check`
Expected: PASS

**Step 2: Run linter**

Run: `cd frontend && npm run lint:fix`
Expected: PASS (or auto-fixed)

**Step 3: Run formatter**

Run: `cd frontend && npm run format`
Expected: Files formatted

**Step 4: Commit any lint/format fixes**

```bash
git add -A
git commit -m "chore: lint and format highlight labels UI"
```

---

## File Summary

**New files (3):**
- `frontend/src/pages/BookPage/common/LabelIndicator.tsx` — dot/chip display component
- `frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/components/LabelEditorPopover.tsx` — popover with text input + color picker
- `frontend/src/pages/BookPage/navigation/HighlightLabelsList.tsx` — sidebar label filter section

**Modified files (6):**
- `frontend/src/theme/Icons.tsx` — add PaletteIcon
- `frontend/src/pages/BookPage/HighlightsTab/HighlightCard.tsx` — add LabelIndicator to footer
- `frontend/src/pages/BookPage/common/HighlightContent.tsx` — add clickable LabelIndicator to metadata
- `frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal.tsx` — wire up LabelEditorPopover
- `frontend/src/routes/book.$bookId.tsx` — add labelId URL param
- `frontend/src/pages/BookPage/BookPage.tsx` — add handleLabelClick
- `frontend/src/pages/BookPage/HighlightsTab/HighlightsTab.tsx` — add label state, filtering, pass to sidebar/mobile
- `frontend/src/pages/BookPage/navigation/MobileNavigation.tsx` — add HighlightLabelsList to Tags drawer
