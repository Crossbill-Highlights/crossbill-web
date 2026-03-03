import type {
  ChapterWithHighlights,
  Flashcard,
  Highlight,
  HighlightTagGroupInBook,
  HighlightTagInBook,
} from '@/api/generated/model';
import { scrollToElementWithHighlight } from '@/components/animations/scrollUtils';
import { SearchBar } from '@/components/inputs/SearchBar.tsx';
import { ContentWithSidebar } from '@/components/layout/Layouts.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { ChapterNav, type ChapterNavigationData } from '@/pages/BookPage/navigation/ChapterNav.tsx';
import { FilterListIcon, SortIcon } from '@/theme/Icons.tsx';
import { Box, Fab, IconButton, Tooltip } from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { flatMap } from 'lodash';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { FilterDrawer, type FilterTab } from '../navigation/FilterDrawer.tsx';
import { HighlightTagsList } from '../navigation/HighlightTagsList.tsx';
import {
  FlashcardChapterList,
  type FlashcardChapterData,
  type FlashcardWithContext,
} from './FlashcardChapterList.tsx';
import { FlashcardEditDialog } from './FlashcardEditDialog.tsx';

const BOOK_FLASHCARDS_KEY = -1;

export const FlashcardsPage = () => {
  const { book, isDesktop, leftSidebarEl, setHasFloatingFilter } = useBookPage();

  const { search: urlSearch, tagId: urlTagId } = useSearch({ from: '/book/$bookId/flashcards' });
  const navigate = useNavigate({ from: '/book/$bookId/flashcards' });

  const searchText = urlSearch || '';
  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(urlTagId);
  const [isReversed, setIsReversed] = useState(false);
  const [editingFlashcard, setEditingFlashcard] = useState<FlashcardWithContext | null>(null);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);

  useEffect(() => {
    setSelectedTagId(urlTagId);
  }, [urlTagId]);

  // Navigation callbacks
  const handleSearch = useCallback(
    (value: string) => {
      navigate({
        search: (prev) => ({ ...prev, search: value || undefined }),
        replace: true,
      });
    },
    [navigate]
  );

  const handleTagClick = useCallback(
    (newTagId: number | null) => {
      setSelectedTagId(newTagId || undefined);
      navigate({
        search: (prev) => ({ ...prev, tagId: newTagId || undefined }),
        replace: true,
      });
    },
    [navigate]
  );

  const handleChapterClick = useCallback(
    (chapterId: number) => {
      if (urlSearch) {
        navigate({
          search: (prev) => ({ ...prev, search: undefined }),
          replace: true,
        });
      }
      scrollToElementWithHighlight(`chapter-${chapterId}`, {
        behavior: 'smooth',
        block: 'start',
      });
    },
    [navigate, urlSearch]
  );

  const bookChapters = book.chapters;

  // Build a map of chapter IDs to chapter names for resolving chapter-linked flashcards
  const chapterNameMap = useMemo(() => {
    const map: Record<number, string> = {};
    for (const ch of bookChapters) {
      map[ch.id] = ch.name || 'Unknown Chapter';
    }
    return map;
  }, [bookChapters]);

  // Extract all flashcards with context from book chapters
  const allFlashcardsWithContext = useMemo((): FlashcardWithContext[] => {
    const highlightFlashcards = flatMap(bookChapters, (chapter: ChapterWithHighlights) =>
      flatMap(chapter.highlights, (highlight: Highlight) =>
        highlight.flashcards.map((flashcard: Flashcard) => ({
          ...flashcard,
          highlight: highlight,
          chapterName: chapter.name || 'Unknown Chapter',
          chapterId: chapter.id,
          highlightTags: highlight.highlight_tags,
        }))
      )
    );

    // book_flashcards includes both truly book-level (no chapter_id) and
    // chapter-linked (chapter_id set, highlight_id null) flashcards
    const bookLevelFlashcards: FlashcardWithContext[] = (book.book_flashcards ?? []).map((fc) => ({
      ...fc,
      highlight: null,
      chapterName: fc.chapter_id
        ? (chapterNameMap[fc.chapter_id] ?? 'Unknown Chapter')
        : 'Book Flashcards',
      chapterId: fc.chapter_id ?? null,
      highlightTags: [],
    }));

    return [...highlightFlashcards, ...bookLevelFlashcards];
  }, [bookChapters, book.book_flashcards, chapterNameMap]);

  // Filter flashcards by tag and search
  const filteredFlashcards = useMemo((): FlashcardWithContext[] => {
    let result = allFlashcardsWithContext;

    // Filter by tag
    if (selectedTagId) {
      result = result.filter((fc) => fc.highlightTags.some((tag) => tag.id === selectedTagId));
    }

    // Filter by search (question or answer)
    if (searchText) {
      const lowerSearch = searchText.toLowerCase();
      result = result.filter(
        (fc) =>
          fc.question.toLowerCase().includes(lowerSearch) ||
          fc.answer.toLowerCase().includes(lowerSearch)
      );
    }

    return result;
  }, [allFlashcardsWithContext, selectedTagId, searchText]);

  // Group flashcards by chapter
  const flashcardChapters = useMemo((): FlashcardChapterData[] => {
    const grouped: Partial<Record<number, FlashcardWithContext[]>> = {};
    for (const fc of filteredFlashcards) {
      const key = fc.chapterId ?? BOOK_FLASHCARDS_KEY;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key]!.push(fc);
    }

    // Separate book-level flashcards from chapter flashcards
    const bookFlashcardsGroup = grouped[BOOK_FLASHCARDS_KEY];
    delete grouped[BOOK_FLASHCARDS_KEY];

    const chapterResults = Object.entries(grouped)
      .filter((entry): entry is [string, FlashcardWithContext[]] => entry[1] !== undefined)
      .map(([chapterId, flashcards]) => ({
        id: Number(chapterId),
        name: flashcards[0].chapterName,
        flashcards,
      }));

    // Append book-level flashcards at the end
    if (bookFlashcardsGroup && bookFlashcardsGroup.length > 0) {
      chapterResults.push({
        id: BOOK_FLASHCARDS_KEY,
        name: 'Book Flashcards',
        flashcards: bookFlashcardsGroup,
      });
    }

    if (isReversed) {
      return [...chapterResults].reverse().map((chapter) => ({
        ...chapter,
        flashcards: [...chapter.flashcards].reverse(),
      }));
    }

    return chapterResults;
  }, [filteredFlashcards, isReversed]);

  // Compute empty message based on state
  const emptyMessage = useMemo(() => {
    if (searchText) {
      return selectedTagId
        ? 'No flashcards found matching your search with the selected tag.'
        : 'No flashcards found matching your search.';
    }
    return selectedTagId
      ? 'No flashcards found with the selected tag.'
      : 'No flashcards yet. Create flashcards from your highlights to start studying.';
  }, [searchText, selectedTagId]);

  const navData = useFlashcardsPageData(
    allFlashcardsWithContext,
    flashcardChapters,
    book.highlight_tags
  );

  // Signal to BookPage that this tab has a floating filter FAB on mobile
  useEffect(() => {
    if (!isDesktop) {
      setHasFloatingFilter(true);
      return () => setHasFloatingFilter(false);
    }
  }, [isDesktop, setHasFloatingFilter]);

  const filterTabs = useFlashcardsFilterTabs({
    navChapters: navData.chapters,
    tags: navData.tags,
    tagGroups: book.highlight_tag_groups,
    bookId: book.id,
    selectedTagId,
    handleChapterClick,
    handleTagClick,
    setFilterDrawerOpen,
  });

  return (
    <>
      {/* Desktop: portal Tags into left sidebar */}
      {isDesktop &&
        leftSidebarEl &&
        createPortal(
          <FlashcardsSidebar
            tags={navData.tags}
            tagGroups={book.highlight_tag_groups}
            bookId={book.id}
            selectedTagId={selectedTagId}
            onTagClick={handleTagClick}
          />,
          leftSidebarEl
        )}

      {/* Content */}
      {isDesktop ? (
        <ContentWithSidebar>
          <Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
              <Box sx={{ flexGrow: 1 }}>
                <SearchBar
                  onSearch={handleSearch}
                  placeholder="Search flashcards..."
                  initialValue={searchText}
                />
              </Box>
              <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
                <IconButton
                  onClick={() => setIsReversed(!isReversed)}
                  sx={{
                    mt: '1px',
                    color: isReversed ? 'primary.main' : 'text.secondary',
                    '&:hover': { color: 'primary.main' },
                  }}
                >
                  <SortIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <FlashcardChapterList
              chapters={flashcardChapters}
              bookId={book.id}
              emptyMessage={emptyMessage}
              animationKey="flashcards"
              onEditFlashcard={setEditingFlashcard}
            />
          </Box>
          <ChapterNav
            chapters={navData.chapters}
            onChapterClick={handleChapterClick}
            countType="flashcard"
          />
        </ContentWithSidebar>
      ) : (
        <>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
            <Box sx={{ flexGrow: 1 }}>
              <SearchBar
                onSearch={handleSearch}
                placeholder="Search flashcards..."
                initialValue={searchText}
              />
            </Box>
            <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
              <IconButton
                onClick={() => setIsReversed(!isReversed)}
                sx={{
                  mt: '1px',
                  color: isReversed ? 'primary.main' : 'text.secondary',
                  '&:hover': { color: 'primary.main' },
                }}
              >
                <SortIcon />
              </IconButton>
            </Tooltip>
          </Box>
          <FlashcardChapterList
            chapters={flashcardChapters}
            bookId={book.id}
            emptyMessage={emptyMessage}
            animationKey="flashcards"
            onEditFlashcard={setEditingFlashcard}
          />
          <Fab
            size="small"
            color="primary"
            aria-label="Open filters"
            onClick={() => setFilterDrawerOpen(true)}
            sx={{
              position: 'fixed',
              bottom: 'calc(80px + env(safe-area-inset-bottom))',
              right: 24,
              zIndex: 1000,
            }}
          >
            <FilterListIcon />
          </Fab>
          <FilterDrawer
            open={filterDrawerOpen}
            onClose={() => setFilterDrawerOpen(false)}
            tabs={filterTabs}
          />
        </>
      )}

      {editingFlashcard && (
        <FlashcardEditDialog
          flashcard={editingFlashcard}
          bookId={book.id}
          open={!!editingFlashcard}
          onClose={() => setEditingFlashcard(null)}
        />
      )}
    </>
  );
};

// --- Extracted subcomponents ---

interface FlashcardsSidebarProps {
  tags: HighlightTagInBook[];
  tagGroups: HighlightTagGroupInBook[];
  bookId: number;
  selectedTagId: number | undefined;
  onTagClick: (tagId: number | null) => void;
}

const FlashcardsSidebar = ({
  tags,
  tagGroups,
  bookId,
  selectedTagId,
  onTagClick,
}: FlashcardsSidebarProps) => (
  <HighlightTagsList
    tags={tags}
    tagGroups={tagGroups}
    bookId={bookId}
    selectedTag={selectedTagId}
    onTagClick={onTagClick}
    hideEmptyGroups
  />
);

interface UseFlashcardsFilterTabsParams {
  navChapters: ChapterNavigationData[];
  tags: HighlightTagInBook[];
  tagGroups: HighlightTagGroupInBook[];
  bookId: number;
  selectedTagId: number | undefined;
  handleChapterClick: (chapterId: number) => void;
  handleTagClick: (tagId: number | null) => void;
  setFilterDrawerOpen: (open: boolean) => void;
}

const useFlashcardsFilterTabs = ({
  navChapters,
  tags,
  tagGroups,
  bookId,
  selectedTagId,
  handleChapterClick,
  handleTagClick,
  setFilterDrawerOpen,
}: UseFlashcardsFilterTabsParams): FilterTab[] =>
  useMemo(
    () => [
      {
        label: 'Chapters',
        content: (
          <ChapterNav
            chapters={navChapters}
            onChapterClick={(id) => {
              handleChapterClick(id);
              setFilterDrawerOpen(false);
            }}
            hideTitle
            countType="flashcard"
          />
        ),
      },
      {
        label: 'Tags',
        content: (
          <HighlightTagsList
            tags={tags}
            tagGroups={tagGroups}
            bookId={bookId}
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
    ],
    [
      navChapters,
      tags,
      handleChapterClick,
      tagGroups,
      bookId,
      selectedTagId,
      handleTagClick,
      setFilterDrawerOpen,
    ]
  );

// --- Private hooks ---

const useFlashcardsPageData = (
  allFlashcardsWithContext: FlashcardWithContext[],
  chapters: FlashcardChapterData[],
  tagsInBook: HighlightTagInBook[] | undefined
) => {
  const tagsWithFlashcards = useMemo(() => {
    if (!tagsInBook) return [];

    const tagIdsWithFlashcards = new Set<number>();
    allFlashcardsWithContext.forEach((fc) =>
      fc.highlightTags.forEach((tag) => tagIdsWithFlashcards.add(tag.id))
    );

    return tagsInBook.filter((tag) => tagIdsWithFlashcards.has(tag.id));
  }, [tagsInBook, allFlashcardsWithContext]);

  const navChapters: ChapterNavigationData[] = useMemo(() => {
    return chapters.map((ch) => ({
      id: ch.id,
      name: ch.name,
      itemCount: ch.flashcards.length,
    }));
  }, [chapters]);

  return {
    chapters: navChapters,
    tags: tagsWithFlashcards,
  };
};
