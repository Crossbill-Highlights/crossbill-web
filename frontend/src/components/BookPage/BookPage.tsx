import { useGetBookDetailsApiV1BooksBookIdGet } from '@/api/generated/books/books';
import { useSearchHighlightsApiV1HighlightsSearchGet } from '@/api/generated/highlights/highlights.ts';
import type { Highlight } from '@/api/generated/model';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { scrollToElementWithHighlight } from '@/components/common/animations/scrollUtils';
import { Alert, Box, Container } from '@mui/material';
import { useNavigate, useParams, useSearch } from '@tanstack/react-router';
import { keyBy } from 'lodash';
import { useMemo, useState } from 'react';
import { ScrollToTopButton } from '../common/ScrollToTopButton';
import { SearchBar } from '../common/SearchBar';
import { Spinner } from '../common/Spinner';
import { BookmarkList } from './components/BookmarkList';
import { BookTitle } from './components/BookTitle';
import { ChapterList } from './components/ChapterList';
import { HighlightTags } from './components/HighlightTags';
import { groupSearchResultsIntoChapters } from './utils/groupSearchResults';

export const BookPage = () => {
  const { bookId } = useParams({ from: '/book/$bookId' });
  const { search, tagId } = useSearch({ from: '/book/$bookId' });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BooksBookIdGet(Number(bookId));

  const navigate = useNavigate({ from: '/book/$bookId' });
  const searchText = search || '';

  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(tagId);

  const handleSearch = (value: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        search: value || undefined,
      }),
      replace: true,
    });
  };

  const handleTagClick = (tagId: number | null) => {
    setSelectedTagId(tagId || undefined);
    navigate({
      search: (prev) => ({
        ...prev,
        tagId: tagId || undefined,
      }),
      replace: true,
    });
  };

  const handleBookmarkClick = (highlightId: number) => {
    // Clear search to ensure the highlight is visible
    if (searchText) {
      navigate({
        search: (prev) => ({
          ...prev,
          search: undefined,
        }),
        replace: true,
      });
    }

    // Scroll to the highlight after a short delay to ensure DOM is ready
    scrollToElementWithHighlight(`highlight-${highlightId}`, { behavior: 'smooth' });
  };

  const { data: searchResults, isLoading: isSearching } =
    useSearchHighlightsApiV1HighlightsSearchGet(
      {
        searchText: searchText || 'placeholder',
        bookId: Number(bookId),
      },
      {
        query: {
          enabled: searchText.length > 0,
        },
      }
    );

  const totalHighlights =
    book?.chapters?.reduce((sum, chapter) => sum + (chapter.highlights?.length || 0), 0) || 0;

  // Show search results or regular chapter view
  const showSearchResults = searchText.length > 0;

  // Create a map of highlight_id -> bookmark for efficient lookup
  const bookmarksByHighlightId = useMemo(
    () => keyBy(book?.bookmarks || [], 'highlight_id'),
    [book?.bookmarks]
  );

  // Filter chapters by selected tag
  const filteredChapters = useMemo(() => {
    const chaptersWithHighlights = (book?.chapters || []).filter(
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
  }, [book?.chapters, selectedTagId]);

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
  const chapters = useMemo(() => {
    if (showSearchResults) {
      return groupSearchResultsIntoChapters(filteredSearchResults);
    }
    return filteredChapters.map((chapter) => ({
      id: chapter.id,
      name: chapter.name || 'Unknown Chapter',
      chapterNumber: chapter.chapter_number ?? undefined,
      highlights: (chapter.highlights || []) as Highlight[],
    }));
  }, [showSearchResults, filteredSearchResults, filteredChapters]);

  // Flat array of all highlights for navigation
  const allHighlights = useMemo(() => {
    return chapters.flatMap((chapter) => chapter.highlights);
  }, [chapters]);

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

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
        }}
      >
        <Container maxWidth="lg">
          <Spinner />
        </Container>
      </Box>
    );
  }

  if (isError || !book) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ pt: 4 }}>
            <Alert severity="error">Failed to load book details. Please try again later.</Alert>
          </Box>
        </Container>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <ScrollToTopButton />
      <FadeInOut ekey={'book-title'}>
        <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3 }, py: 4 }}>
          {/* Mobile Layout */}
          <Box sx={{ display: { xs: 'block', lg: 'none' } }}>
            <BookTitle book={book} highlightCount={totalHighlights} />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 3 }}>
              <HighlightTags
                tags={book.highlight_tags || []}
                tagGroups={book.highlight_tag_groups || []}
                bookId={book.id}
                selectedTag={selectedTagId}
                onTagClick={handleTagClick}
              />
              <BookmarkList
                bookmarks={book.bookmarks || []}
                allHighlights={allHighlights}
                onBookmarkClick={handleBookmarkClick}
              />
            </Box>
            <SearchBar
              onSearch={handleSearch}
              placeholder="Search highlights..."
              initialValue={searchText}
            />
            <ChapterList
              chapters={chapters}
              bookId={book.id}
              bookmarksByHighlightId={bookmarksByHighlightId}
              allHighlights={allHighlights}
              isLoading={showSearchResults && isSearching}
              emptyMessage={emptyMessage}
              animationKey={`chapters-${showSearchResults ? 'search' : 'view'}-${selectedTagId ?? 'all'}`}
            />
          </Box>

          {/* Desktop 3-Column Layout */}
          <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
            {/* Book Details + Search Bar - Centered with middle column */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: '250px 1fr 250px',
                gap: 4,
              }}
            >
              <Box /> {/* Empty left spacer */}
              <Box>
                <BookTitle book={book} highlightCount={totalHighlights} />
                <SearchBar
                  onSearch={handleSearch}
                  placeholder="Search highlights..."
                  initialValue={searchText}
                />
              </Box>
              <Box /> {/* Empty right spacer */}
            </Box>

            {/* 3-Column Content Grid */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: '250px 1fr 250px',
                gap: 4,
                alignItems: 'start',
              }}
            >
              {/* Left Column - Tags */}
              <Box sx={{ position: 'sticky', top: 80 }}>
                <HighlightTags
                  tags={book.highlight_tags || []}
                  tagGroups={book.highlight_tag_groups || []}
                  bookId={book.id}
                  selectedTag={selectedTagId}
                  onTagClick={handleTagClick}
                />
              </Box>

              {/* Middle Column - Chapter List */}
              <ChapterList
                chapters={chapters}
                bookId={book.id}
                bookmarksByHighlightId={bookmarksByHighlightId}
                allHighlights={allHighlights}
                isLoading={showSearchResults && isSearching}
                emptyMessage={emptyMessage}
                animationKey={`chapters-${showSearchResults ? 'search' : 'view'}-${selectedTagId ?? 'all'}`}
              />

              {/* Right Column - Bookmarks */}
              <Box sx={{ position: 'sticky', top: 80 }}>
                <BookmarkList
                  bookmarks={book.bookmarks || []}
                  allHighlights={allHighlights}
                  onBookmarkClick={handleBookmarkClick}
                />
              </Box>
            </Box>
          </Box>
        </Container>
      </FadeInOut>
    </Box>
  );
};
