import { useGetBookDetailsApiV1BookBookIdGet } from '@/api/generated/books/books.ts';
import { useSearchHighlightsApiV1HighlightsSearchGet } from '@/api/generated/highlights/highlights.ts';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { scrollToElementWithHighlight } from '@/components/common/animations/scrollUtils';
import { Alert, Box, Container, Typography } from '@mui/material';
import { useNavigate, useParams, useSearch } from '@tanstack/react-router';
import { keyBy } from 'lodash';
import { useState } from 'react';
import { SearchBar } from '../common/SearchBar';
import { SectionTitle } from '../common/SectionTitle';
import { Spinner } from '../common/Spinner';
import { BookmarkList } from './components/BookmarkList';
import { BookTitle } from './components/BookTitle';
import { HighlightCard } from './components/HighlightCard';
import { HighlightTags } from './components/HighlightTags';
import { SearchResults } from './components/SearchResults';

export const BookPage = () => {
  const { bookId } = useParams({ from: '/book/$bookId' });
  const { search, tagId } = useSearch({ from: '/book/$bookId' });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BookBookIdGet(Number(bookId));

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

  // Create a map of highlight_id -> bookmark for efficient lookup
  const bookmarksByHighlightId = keyBy(book.bookmarks || [], 'highlight_id');

  const chapters = (book?.chapters || []).filter(
    (chapter) => chapter.highlights && chapter.highlights.length > 0
  );

  // Filter chapters by selected tag
  const filteredChapters = selectedTagId
    ? chapters
        .map((chapter) => ({
          ...chapter,
          highlights: chapter.highlights?.filter((highlight) =>
            highlight.highlight_tags?.some((tag) => tag.id === selectedTagId)
          ),
        }))
        .filter((chapter) => chapter.highlights && chapter.highlights.length > 0)
    : chapters;

  // Create a flat array of all highlights for navigation
  const allFilteredHighlights = filteredChapters.flatMap((chapter) => chapter.highlights || []);

  // Filter search results by selected tag
  const filteredSearchResults = selectedTagId
    ? searchResults?.highlights?.filter((highlight) =>
        highlight.highlight_tags?.some((tag) => tag.id === selectedTagId)
      )
    : searchResults?.highlights;

  // Show search results or regular chapter view
  const showSearchResults = searchText.length > 0;

  return (
    <Box
      sx={{
        minHeight: '100vh',
      }}
    >
      <FadeInOut ekey={'book-title'}>
        <Container maxWidth="lg" sx={{ px: { xs: 2, sm: 3 }, py: 4 }}>
          {/* Book Info Card */}
          <BookTitle book={book} highlightCount={totalHighlights} />

          {/* Tags (Mobile only - above search bar) */}
          <Box sx={{ display: { xs: 'block', lg: 'none' }, mb: 3 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <HighlightTags
                tags={book.highlight_tags || []}
                tagGroups={book.highlight_tag_groups || []}
                bookId={book.id}
                selectedTag={selectedTagId}
                onTagClick={handleTagClick}
              />
              <BookmarkList
                bookmarks={book.bookmarks || []}
                allHighlights={allFilteredHighlights}
                onBookmarkClick={handleBookmarkClick}
              />
            </Box>
          </Box>

          {/* Search Bar - Aligned with content column on desktop */}
          <Box
            sx={{
              maxWidth: { xs: '100%', lg: 'calc(100% - 300px - 32px)' }, // Subtract sidebar width + gap
            }}
          >
            <SearchBar
              onSearch={handleSearch}
              placeholder="Search highlights..."
              initialValue={searchText}
            />
          </Box>

          {/* Search Results */}
          {showSearchResults && (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', lg: '1fr 300px' },
                gap: 4,
                alignItems: 'start',
              }}
            >
              <SearchResults
                isSearching={isSearching}
                highlights={filteredSearchResults}
                searchText={searchText}
                bookId={book.id}
                bookmarksByHighlightId={bookmarksByHighlightId}
                selectedTagId={selectedTagId}
              />

              {/* Sidebar - Tags (Desktop only) */}
              <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <HighlightTags
                    tags={book.highlight_tags || []}
                    tagGroups={book.highlight_tag_groups || []}
                    bookId={book.id}
                    selectedTag={selectedTagId}
                    onTagClick={handleTagClick}
                  />
                  <BookmarkList
                    bookmarks={book.bookmarks || []}
                    allHighlights={filteredSearchResults || []}
                    onBookmarkClick={handleBookmarkClick}
                  />
                </Box>
              </Box>
            </Box>
          )}

          {/* Regular Chapter View (when not searching) */}
          {!showSearchResults && (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', lg: '1fr 300px' },
                gap: 4,
                alignItems: 'start',
              }}
            >
              <FadeInOut ekey={`chapters-view-${selectedTagId ?? 'all'}`}>
                {/* Main content - Highlights */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {filteredChapters && filteredChapters.length === 0 && (
                    <Typography variant="body1" color="text.secondary">
                      {selectedTagId
                        ? 'No highlights found with the selected tag.'
                        : 'No chapters found for this book.'}
                    </Typography>
                  )}

                  {filteredChapters.map((chapter) => (
                    <Box key={chapter.id}>
                      {/* Chapter Header */}
                      <SectionTitle showDivider>{chapter.name}</SectionTitle>

                      {/* Highlights in this chapter */}
                      {chapter.highlights && chapter.highlights.length > 0 ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                          {chapter.highlights.map((highlight) => {
                            const highlightIndex = allFilteredHighlights.findIndex(
                              (h) => h.id === highlight.id
                            );
                            return (
                              <HighlightCard
                                key={highlight.id}
                                highlight={highlight}
                                bookId={book.id}
                                bookmark={bookmarksByHighlightId[highlight.id]}
                                bookmarksByHighlightId={bookmarksByHighlightId}
                                allHighlights={allFilteredHighlights}
                                currentIndex={highlightIndex}
                              />
                            );
                          })}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ pl: 0.5 }}>
                          No highlights found in this chapter.
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Box>
              </FadeInOut>

              {/* Sidebar - Tags (Desktop only) */}
              <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <HighlightTags
                    tags={book.highlight_tags || []}
                    tagGroups={book.highlight_tag_groups || []}
                    bookId={book.id}
                    selectedTag={selectedTagId}
                    onTagClick={handleTagClick}
                  />
                  <BookmarkList
                    bookmarks={book.bookmarks || []}
                    allHighlights={allFilteredHighlights}
                    onBookmarkClick={handleBookmarkClick}
                  />
                </Box>
              </Box>
            </Box>
          )}
        </Container>
      </FadeInOut>
    </Box>
  );
};
