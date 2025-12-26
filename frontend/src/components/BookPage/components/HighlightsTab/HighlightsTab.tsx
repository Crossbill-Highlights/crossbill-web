import { useGetHighlightTagsApiV1BooksBookIdHighlightTagsGet } from '@/api/generated/books/books.ts';
import { useSearchHighlightsApiV1HighlightsSearchGet } from '@/api/generated/highlights/highlights.ts';
import type { BookDetails, Bookmark, Highlight, HighlightTagInBook } from '@/api/generated/model';
import { scrollToElementWithHighlight } from '@/components/common/animations/scrollUtils.ts';
import { SortIcon } from '@/components/common/Icons.tsx';
import { SearchBar } from '@/components/common/SearchBar.tsx';
import { Box, IconButton, Tooltip } from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { keyBy } from 'lodash';
import { useEffect, useMemo, useState } from 'react';
import { useHighlightModal } from '../../hooks/useHighlightModal.ts';
import { groupSearchResultsIntoChapters } from '../../utils/groupSearchResults.ts';
import { BookmarkList } from '../BookmarkList.tsx';
import { HighlightTags } from '../HighlightTags.tsx';
import { ChapterList, type ChapterData } from './ChapterList.tsx';
import { ChapterNav } from './ChapterNav.tsx';
import { HighlightViewModal } from './HighlightViewModal';

interface HighlightsTabProps {
  book: BookDetails;
  isDesktop: boolean;
  isMobile: boolean;
}

export const HighlightsTab = ({ book, isDesktop, isMobile }: HighlightsTabProps) => {
  const { search: urlSearch, tagId: urlTagId } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  const searchText = urlSearch || '';
  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(urlTagId);
  const [isReversed, setIsReversed] = useState(false);

  useEffect(() => {
    setSelectedTagId(urlTagId);
  }, [urlTagId]);

  // Fetch available tags for the highlight modal
  const { data: tagsResponse } = useGetHighlightTagsApiV1BooksBookIdHighlightTagsGet(book.id);

  const handleSearch = (value: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        search: value || undefined,
      }),
      replace: true,
    });
  };

  const handleTagClick = (newTagId: number | null) => {
    setSelectedTagId(newTagId || undefined);
    navigate({
      search: (prev) => ({
        ...prev,
        tagId: newTagId || undefined,
      }),
      replace: true,
    });
  };

  const handleBookmarkClick = (highlightId: number) => {
    if (searchText) {
      navigate({
        search: (prev) => ({
          ...prev,
          search: undefined,
        }),
        replace: true,
      });
    }
    scrollToElementWithHighlight(`highlight-${highlightId}`, { behavior: 'smooth' });
  };

  const handleChapterClick = (chapterId: number | string) => {
    if (searchText) {
      navigate({
        search: (prev) => ({
          ...prev,
          search: undefined,
        }),
        replace: true,
      });
    }
    scrollToElementWithHighlight(`chapter-${chapterId}`, { behavior: 'smooth', block: 'start' });
  };

  // Highlight search
  const { data: searchResults, isLoading: isSearching } =
    useSearchHighlightsApiV1HighlightsSearchGet(
      {
        searchText: searchText || 'placeholder',
        bookId: book.id,
      },
      {
        query: {
          enabled: searchText.length > 0,
        },
      }
    );

  const showSearchResults = searchText.length > 0;

  const bookmarksByHighlightId = useMemo(
    () => keyBy(book.bookmarks || [], 'highlight_id'),
    [book.bookmarks]
  );

  // Filter chapters by selected tag
  const filteredChapters = useMemo(() => {
    const chaptersWithHighlights = (book.chapters || []).filter(
      (chapter) => chapter.highlights && chapter.highlights.length > 0
    );

    if (!selectedTagId) {
      return chaptersWithHighlights;
    }

    return chaptersWithHighlights
      .map((chapter) => ({
        ...chapter,
        highlights: chapter.highlights?.filter((highlight) =>
          highlight.highlight_tags?.some((tag) => tag.id === selectedTagId)
        ),
      }))
      .filter((chapter) => chapter.highlights && chapter.highlights.length > 0);
  }, [book.chapters, selectedTagId]);

  // Filter search results by selected tag
  const filteredSearchResults = useMemo(() => {
    if (!selectedTagId) {
      return searchResults?.highlights;
    }
    return searchResults?.highlights?.filter((highlight) =>
      highlight.highlight_tags?.some((tag) => tag.id === selectedTagId)
    );
  }, [searchResults?.highlights, selectedTagId]);

  // Unified chapter data for both search and regular views
  const chapters: ChapterData[] = useMemo(() => {
    let result;
    if (showSearchResults) {
      result = groupSearchResultsIntoChapters(filteredSearchResults);
    } else {
      result = filteredChapters.map((chapter) => ({
        id: chapter.id,
        name: chapter.name || 'Unknown Chapter',
        chapterNumber: chapter.chapter_number ?? undefined,
        highlights: (chapter.highlights || []) as Highlight[],
      }));
    }

    if (isReversed) {
      return [...result].reverse().map((chapter) => ({
        ...chapter,
        highlights: [...chapter.highlights].reverse(),
      }));
    }

    return result;
  }, [showSearchResults, filteredSearchResults, filteredChapters, isReversed]);

  // Flat array of all highlights for navigation
  const allHighlights = useMemo(() => {
    return chapters.flatMap((chapter) => chapter.highlights);
  }, [chapters]);

  // Use the highlight modal hook for URL-synced modal state
  const {
    openHighlightId,
    currentHighlight,
    currentHighlightIndex,
    handleOpenHighlight,
    handleCloseHighlight,
    handleModalNavigate,
  } = useHighlightModal({ allHighlights, isMobile });

  // Compute empty message based on state
  const emptyMessage = useMemo(() => {
    if (showSearchResults) {
      return selectedTagId
        ? 'No highlights found matching your search with the selected tag.'
        : 'No highlights found matching your search.';
    }
    return selectedTagId
      ? 'No highlights found with the selected tag.'
      : 'No chapters found for this book.';
  }, [showSearchResults, selectedTagId]);

  const tags = book.highlight_tags || [];

  return (
    <>
      {/* Mobile Layout */}
      {!isDesktop && (
        <MobileHighlightsContent
          searchText={searchText}
          onSearch={handleSearch}
          isReversed={isReversed}
          onToggleReverse={() => setIsReversed(!isReversed)}
          chapters={chapters}
          bookmarksByHighlightId={bookmarksByHighlightId}
          isSearching={showSearchResults && isSearching}
          emptyMessage={emptyMessage}
          onOpenHighlight={handleOpenHighlight}
        />
      )}

      {/* Desktop Layout */}
      {isDesktop && (
        <DesktopHighlightsContent
          book={book}
          tags={tags}
          selectedTagId={selectedTagId}
          onTagClick={handleTagClick}
          searchText={searchText}
          onSearch={handleSearch}
          isReversed={isReversed}
          onToggleReverse={() => setIsReversed(!isReversed)}
          chapters={chapters}
          bookmarksByHighlightId={bookmarksByHighlightId}
          allHighlights={allHighlights}
          isSearching={showSearchResults && isSearching}
          emptyMessage={emptyMessage}
          onOpenHighlight={handleOpenHighlight}
          onBookmarkClick={handleBookmarkClick}
          onChapterClick={handleChapterClick}
        />
      )}

      {/* Highlight Modal */}
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

// Mobile content component
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
    <ChapterList
      chapters={chapters}
      bookmarksByHighlightId={bookmarksByHighlightId}
      isLoading={isSearching}
      emptyMessage={emptyMessage}
      animationKey={`chapters-highlights`}
      onOpenHighlight={onOpenHighlight}
    />
  </>
);

// Desktop content component
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
  bookmarksByHighlightId: Record<number, Bookmark>;
  allHighlights: Highlight[];
  isSearching: boolean;
  emptyMessage: string;
  onOpenHighlight: (highlightId: number) => void;
  onBookmarkClick: (highlightId: number) => void;
  onChapterClick: (chapterId: number | string) => void;
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
  bookmarksByHighlightId,
  allHighlights,
  isSearching,
  emptyMessage,
  onOpenHighlight,
  onBookmarkClick,
  onChapterClick,
}: DesktopHighlightsContentProps) => (
  <Box
    sx={{
      display: 'grid',
      gridTemplateColumns: '280px 1fr 280px',
      gap: 4,
      alignItems: 'start',
    }}
  >
    {/* Left Column - Tags */}
    <HighlightTags
      tags={tags}
      tagGroups={book.highlight_tag_groups || []}
      bookId={book.id}
      selectedTag={selectedTagId}
      onTagClick={onTagClick}
    />

    {/* Middle Column - Search + Content */}
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
      <ChapterList
        chapters={chapters}
        bookmarksByHighlightId={bookmarksByHighlightId}
        isLoading={isSearching}
        emptyMessage={emptyMessage}
        animationKey={`chapters-highlights`}
        onOpenHighlight={onOpenHighlight}
      />
    </Box>

    {/* Right Column - Bookmarks + Chapters */}
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <BookmarkList
        bookmarks={book.bookmarks || []}
        allHighlights={allHighlights}
        onBookmarkClick={onBookmarkClick}
      />
      <ChapterNav chapters={chapters} onChapterClick={onChapterClick} />
    </Box>
  </Box>
);

// Export types and data needed by MobileNavigation
// eslint-disable-next-line react-refresh/only-export-components
export const useHighlightsTabData = (book: BookDetails) => {
  const { search: urlSearch, tagId: urlTagId } = useSearch({ from: '/book/$bookId' });
  const searchText = urlSearch || '';
  const selectedTagId = urlTagId;

  const filteredChapters = useMemo(() => {
    const chaptersWithHighlights = (book.chapters || []).filter(
      (chapter) => chapter.highlights && chapter.highlights.length > 0
    );

    if (!selectedTagId) {
      return chaptersWithHighlights;
    }

    return chaptersWithHighlights
      .map((chapter) => ({
        ...chapter,
        highlights: chapter.highlights?.filter((highlight) =>
          highlight.highlight_tags?.some((tag) => tag.id === selectedTagId)
        ),
      }))
      .filter((chapter) => chapter.highlights && chapter.highlights.length > 0);
  }, [book.chapters, selectedTagId]);

  const chapters: ChapterData[] = useMemo(() => {
    return filteredChapters.map((chapter) => ({
      id: chapter.id,
      name: chapter.name || 'Unknown Chapter',
      chapterNumber: chapter.chapter_number ?? undefined,
      highlights: (chapter.highlights || []) as Highlight[],
    }));
  }, [filteredChapters]);

  const allHighlights = useMemo(() => {
    return chapters.flatMap((chapter) => chapter.highlights);
  }, [chapters]);

  return {
    chapters,
    allHighlights,
    tags: book.highlight_tags || [],
    searchText,
    selectedTagId,
  };
};
