import {
  useGetHighlightTagsApiV1BooksBookIdHighlightTagsGet,
  useSearchBookHighlightsApiV1BooksBookIdHighlightsGet,
} from '@/api/generated/books/books.ts';
import type {
  BookDetails,
  Bookmark,
  ChapterWithHighlights,
  Highlight,
  HighlightTagInBook,
} from '@/api/generated/model';
import { useHighlightModal } from '@/pages/BookPage/HighlightsTab/hooks/useHighlightModal.ts';
import { SortIcon } from '@/components/Icons.tsx';
import { SearchBar } from '@/components/SearchBar.tsx';
import { ThreeColumnLayout } from '@/components/layout/Layouts.tsx';
import { Box, IconButton, Tooltip } from '@mui/material';
import { useSearch } from '@tanstack/react-router';
import { keyBy } from 'lodash';
import { useEffect, useMemo, useState } from 'react';
import { BookmarkList } from '../navigation/BookmarkList.tsx';
import { ChapterNav, ChapterNavigationData } from '../navigation/ChapterNav.tsx';
import { HighlightTagsList } from '../navigation/HighlightTagsList.tsx';
import { MobileNavigation } from '../navigation/MobileNavigation.tsx';
import { HighlightsList, type ChapterData } from './HighlightsList.tsx';
import { HighlightViewModal } from './HighlightViewModal';

interface HighlightsTabProps {
  book: BookDetails;
  isDesktop: boolean;
  onSearch: (value: string) => void;
  onTagClick: (tagId: number | null) => void;
  onBookmarkClick: (highlightId: number) => void;
  onChapterClick: (chapterId: number) => void;
}

export const HighlightsTab = ({
  book,
  isDesktop,
  onSearch,
  onTagClick,
  onBookmarkClick,
  onChapterClick,
}: HighlightsTabProps) => {
  const { search: urlSearch, tagId: urlTagId } = useSearch({ from: '/book/$bookId' });

  const searchText = urlSearch || '';
  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(urlTagId);
  const [isReversed, setIsReversed] = useState(false);

  useEffect(() => {
    setSelectedTagId(urlTagId);
  }, [urlTagId]);

  // Fetch available tags for the highlight modal
  const { data: tagsResponse } = useGetHighlightTagsApiV1BooksBookIdHighlightTagsGet(book.id);

  const handleTagClick = (newTagId: number | null) => {
    setSelectedTagId(newTagId || undefined);
    onTagClick(newTagId);
  };

  const bookSearch = useBookSearch(book.id, searchText);

  const bookmarksByHighlightId = useMemo(
    () => keyBy(book.bookmarks, 'highlight_id'),
    [book.bookmarks]
  );

  const chapters: ChapterData[] = useMemo(() => {
    const toFilter = bookSearch.showSearchResults
      ? bookSearch.chapters
      : book.chapters.filter((chapter) => chapter.highlights.length > 0);

    const result = filterChaptersByTag(selectedTagId, toFilter).map((chapter) => ({
      id: chapter.id,
      name: chapter.name || 'Unknown Chapter',
      chapterNumber: chapter.chapter_number ?? undefined,
      highlights: chapter.highlights,
    }));

    if (isReversed) {
      return [...result].reverse().map((chapter) => ({
        ...chapter,
        highlights: [...chapter.highlights].reverse(),
      }));
    }

    return result;
  }, [bookSearch.showSearchResults, bookSearch.chapters, isReversed, book.chapters, selectedTagId]);

  const allHighlights = useMemo(() => {
    return chapters.flatMap((chapter) => chapter.highlights);
  }, [chapters]);

  const {
    openHighlightId,
    currentHighlight,
    currentHighlightIndex,
    handleOpenHighlight,
    handleCloseHighlight,
    handleModalNavigate,
  } = useHighlightModal({ allHighlights, isMobile: !isDesktop });

  const tags = book.highlight_tags;

  const navData = useHighlightsTabData(chapters);

  const emptyMessage = useMemo(() => {
    if (bookSearch.showSearchResults) {
      return selectedTagId
        ? 'No highlights found matching your search with the selected tag.'
        : 'No highlights found matching your search.';
    }
    return selectedTagId
      ? 'No highlights found with the selected tag.'
      : 'No chapters found for this book.';
  }, [bookSearch.showSearchResults, selectedTagId]);

  return (
    <>
      {!isDesktop && (
        <>
          <MobileHighlightsContent
            searchText={searchText}
            onSearch={onSearch}
            isReversed={isReversed}
            onToggleReverse={() => setIsReversed(!isReversed)}
            chapters={chapters}
            bookmarksByHighlightId={bookmarksByHighlightId}
            isSearching={bookSearch.isSearching}
            emptyMessage={emptyMessage}
            onOpenHighlight={handleOpenHighlight}
          />
          <MobileNavigation
            book={book}
            onTagClick={handleTagClick}
            selectedTag={selectedTagId}
            bookmarks={book.bookmarks}
            allHighlights={allHighlights}
            onBookmarkClick={onBookmarkClick}
            chapters={navData.chapters}
            onChapterClick={onChapterClick}
            displayTags={tags}
            currentTab="highlights"
          />
        </>
      )}

      {isDesktop && (
        <DesktopHighlightsContent
          book={book}
          tags={tags}
          selectedTagId={selectedTagId}
          onTagClick={handleTagClick}
          searchText={searchText}
          onSearch={onSearch}
          isReversed={isReversed}
          onToggleReverse={() => setIsReversed(!isReversed)}
          chapters={chapters}
          navChapters={navData.chapters}
          bookmarksByHighlightId={bookmarksByHighlightId}
          allHighlights={allHighlights}
          isSearching={bookSearch.isSearching}
          emptyMessage={emptyMessage}
          onOpenHighlight={handleOpenHighlight}
          onBookmarkClick={onBookmarkClick}
          onChapterClick={onChapterClick}
        />
      )}

      {currentHighlight && (
        <HighlightViewModal
          highlight={currentHighlight}
          bookId={book.id}
          open={!!openHighlightId}
          onClose={handleCloseHighlight}
          availableTags={tagsResponse?.tags || []}
          bookmarksByHighlightId={bookmarksByHighlightId}
          allHighlights={allHighlights}
          currentIndex={currentHighlightIndex}
          onNavigate={handleModalNavigate}
        />
      )}
    </>
  );
};

interface MobileHighlightsContentProps {
  searchText: string;
  onSearch: (value: string) => void;
  isReversed: boolean;
  onToggleReverse: () => void;
  chapters: ChapterData[];
  bookmarksByHighlightId: Record<number, Bookmark>;
  isSearching: boolean;
  emptyMessage: string;
  onOpenHighlight: (highlightId: number) => void;
}

const MobileHighlightsContent = ({
  searchText,
  onSearch,
  isReversed,
  onToggleReverse,
  chapters,
  bookmarksByHighlightId,
  isSearching,
  emptyMessage,
  onOpenHighlight,
}: MobileHighlightsContentProps) => (
  <>
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
      <Box sx={{ flexGrow: 1 }}>
        <SearchBar
          onSearch={onSearch}
          placeholder="Search highlights..."
          initialValue={searchText}
        />
      </Box>
      <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
        <IconButton
          onClick={onToggleReverse}
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
    <HighlightsList
      chapters={chapters}
      bookmarksByHighlightId={bookmarksByHighlightId}
      isLoading={isSearching}
      emptyMessage={emptyMessage}
      animationKey={`chapters-highlights`}
      onOpenHighlight={onOpenHighlight}
    />
  </>
);

interface DesktopHighlightsContentProps {
  book: BookDetails;
  tags: HighlightTagInBook[];
  selectedTagId: number | undefined;
  onTagClick: (tagId: number | null) => void;
  searchText: string;
  onSearch: (value: string) => void;
  isReversed: boolean;
  onToggleReverse: () => void;
  chapters: ChapterData[];
  navChapters: ChapterNavigationData[];
  bookmarksByHighlightId: Record<number, Bookmark>;
  allHighlights: Highlight[];
  isSearching: boolean;
  emptyMessage: string;
  onOpenHighlight: (highlightId: number) => void;
  onBookmarkClick: (highlightId: number) => void;
  onChapterClick: (chapterId: number) => void;
}

const DesktopHighlightsContent = ({
  book,
  tags,
  selectedTagId,
  onTagClick,
  searchText,
  onSearch,
  isReversed,
  onToggleReverse,
  chapters,
  navChapters,
  bookmarksByHighlightId,
  allHighlights,
  isSearching,
  emptyMessage,
  onOpenHighlight,
  onBookmarkClick,
  onChapterClick,
}: DesktopHighlightsContentProps) => (
  <ThreeColumnLayout>
    <HighlightTagsList
      tags={tags}
      tagGroups={book.highlight_tag_groups}
      bookId={book.id}
      selectedTag={selectedTagId}
      onTagClick={onTagClick}
    />

    <Box>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
        <Box sx={{ flexGrow: 1 }}>
          <SearchBar
            onSearch={onSearch}
            placeholder="Search highlights..."
            initialValue={searchText}
          />
        </Box>
        <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
          <IconButton
            onClick={onToggleReverse}
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
      <HighlightsList
        chapters={chapters}
        bookmarksByHighlightId={bookmarksByHighlightId}
        isLoading={isSearching}
        emptyMessage={emptyMessage}
        animationKey={`chapters-highlights`}
        onOpenHighlight={onOpenHighlight}
      />
    </Box>

    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <BookmarkList
        bookmarks={book.bookmarks}
        allHighlights={allHighlights}
        onBookmarkClick={onBookmarkClick}
      />
      <ChapterNav chapters={navChapters} onChapterClick={onChapterClick} countType="highlight" />
    </Box>
  </ThreeColumnLayout>
);

const useHighlightsTabData = (chapters: ChapterData[]) => {
  const navChapters: ChapterNavigationData[] = useMemo(() => {
    return chapters.map((chapter) => ({
      id: chapter.id,
      name: chapter.name,
      itemCount: chapter.highlights.length,
    }));
  }, [chapters]);

  return {
    chapters: navChapters,
  };
};

const useBookSearch = (bookId: number, searchText: string) => {
  const { data: searchResults, isLoading: isSearching } =
    useSearchBookHighlightsApiV1BooksBookIdHighlightsGet(
      bookId,
      {
        searchText: searchText || 'placeholder',
      },
      {
        query: {
          enabled: searchText.length > 0,
        },
      }
    );

  const showSearchResults = searchText.length > 0;

  return {
    showSearchResults,
    chapters: searchResults?.chapters || [],
    isSearching: isSearching && showSearchResults,
  };
};

function filterChaptersByTag(
  selectedTagId: number | undefined,
  chaptersWithHighlights: ChapterWithHighlights[]
) {
  if (!selectedTagId) {
    return chaptersWithHighlights;
  }

  return chaptersWithHighlights
    .map((chapter) => ({
      ...chapter,
      highlights: chapter.highlights.filter((highlight) =>
        highlight.highlight_tags.some((tag) => tag.id === selectedTagId)
      ),
    }))
    .filter((chapter) => chapter.highlights.length > 0);
}
