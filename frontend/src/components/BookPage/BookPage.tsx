import {
  getGetRecentlyViewedBooksApiV1BooksRecentlyViewedGetQueryKey,
  useGetBookDetailsApiV1BooksBookIdGet,
} from '@/api/generated/books/books';
import type { BookDetails } from '@/api/generated/model';
import {
  FlashcardsTab,
  useFlashcardsTabData,
} from '@/components/BookPage/components/FlashcardsTab/FlashcardsTab.tsx';
import {
  HighlightsTab,
  useHighlightsTabData,
} from '@/components/BookPage/components/HighlightsTab/HighlightsTab.tsx';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { scrollToElementWithHighlight } from '@/components/common/animations/scrollUtils';
import { FlashcardsIcon, HighlightsIcon } from '@/components/common/Icons.tsx';
import { queryClient } from '@/lib/queryClient';
import {
  Alert,
  Box,
  Container,
  Tab,
  Tabs,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useNavigate, useParams, useSearch } from '@tanstack/react-router';
import { flatMap } from 'lodash';
import { useEffect, useMemo } from 'react';
import { ScrollToTopButton } from '../common/ScrollToTopButton';
import { Spinner } from '../common/Spinner';
import { BookTitle } from './components/BookTitle';
import { MobileNavigation } from './components/MobileNavigation.tsx';

type TabValue = 'highlights' | 'flashcards';

export const BookPage = () => {
  const { bookId } = useParams({ from: '/book/$bookId' });
  const { tab } = useSearch({ from: '/book/$bookId' });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BooksBookIdGet(Number(bookId));

  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const navigate = useNavigate({ from: '/book/$bookId' });
  const activeTab: TabValue = tab || 'highlights';

  // Update recently viewed on mount
  useEffect(() => {
    if (book) {
      void queryClient.invalidateQueries({
        queryKey: getGetRecentlyViewedBooksApiV1BooksRecentlyViewedGetQueryKey(),
      });
    }
  });

  const handleTabChange = (_event: React.SyntheticEvent, newValue: TabValue) => {
    navigate({
      search: (prev) => ({
        ...prev,
        tab: newValue === 'highlights' ? undefined : newValue,
        search: undefined,
        tagId: undefined,
      }),
      replace: true,
    });
  };

  // Calculate totals for tab labels
  const totalHighlights = useMemo(() => {
    return (
      book?.chapters?.reduce((sum, chapter) => sum + (chapter.highlights?.length || 0), 0) || 0
    );
  }, [book?.chapters]);

  const bookChapters = book?.chapters;
  const totalFlashcards = useMemo(() => {
    if (!bookChapters) return 0;
    return flatMap(bookChapters, (chapter) =>
      flatMap(chapter.highlights || [], (highlight) => highlight.flashcards || [])
    ).length;
  }, [bookChapters]);

  if (isLoading) {
    return (
      <Box sx={{ minHeight: '100vh' }}>
        <Box sx={{ px: { xs: 2, sm: 3, lg: 4 }, maxWidth: '1400px', mx: 'auto' }}>
          <Spinner />
        </Box>
      </Box>
    );
  }

  if (isError || !book) {
    return (
      <Box sx={{ minHeight: '100vh' }}>
        <Box sx={{ px: { xs: 2, sm: 3, lg: 4 }, maxWidth: '1400px', mx: 'auto' }}>
          <Box sx={{ pt: 4 }}>
            <Alert severity="error">Failed to load book details. Please try again later.</Alert>
          </Box>
        </Box>
      </Box>
    );
  }

  const TabsComponent = (
    <Tabs
      value={activeTab}
      onChange={handleTabChange}
      sx={{
        mb: 3,
        '& .MuiTabs-indicator': {
          backgroundColor: 'primary.main',
        },
      }}
    >
      <Tab
        value="highlights"
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HighlightsIcon sx={{ fontSize: 20 }} />
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Highlights ({totalHighlights})
            </Typography>
          </Box>
        }
        sx={{ textTransform: 'none' }}
      />
      <Tab
        value="flashcards"
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FlashcardsIcon sx={{ fontSize: 20 }} />
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Flashcards ({totalFlashcards})
            </Typography>
          </Box>
        }
        sx={{ textTransform: 'none' }}
      />
    </Tabs>
  );

  return (
    <Container sx={{ minHeight: '100vh' }} maxWidth="xl">
      <ScrollToTopButton />
      <FadeInOut ekey={'book-title'}>
        {/* Mobile Layout */}
        {!isDesktop && (
          <>
            <Box sx={{ py: 8, maxWidth: '800px', mx: 'auto' }}>
              <BookTitle book={book} highlightCount={totalHighlights} />
              {TabsComponent}

              {activeTab === 'highlights' ? (
                <HighlightsTab book={book} isDesktop={false} isMobile={isMobile} />
              ) : (
                <FlashcardsTab book={book} isDesktop={false} />
              )}
            </Box>
            <MobileNavigationWrapper book={book} activeTab={activeTab} />
          </>
        )}

        {/* Desktop Layout */}
        {isDesktop && (
          <Box sx={{ px: 4, py: 4 }}>
            <BookTitle book={book} highlightCount={totalHighlights} />
            {TabsComponent}

            {activeTab === 'highlights' ? (
              <HighlightsTab book={book} isDesktop={true} isMobile={false} />
            ) : (
              <FlashcardsTab book={book} isDesktop={true} />
            )}
          </Box>
        )}
      </FadeInOut>
    </Container>
  );
};

// Wrapper component that uses the appropriate hooks based on active tab
interface MobileNavigationWrapperProps {
  book: BookDetails;
  activeTab: TabValue;
}

const MobileNavigationWrapper = ({ book, activeTab }: MobileNavigationWrapperProps) => {
  const navigate = useNavigate({ from: '/book/$bookId' });
  const { search: urlSearch } = useSearch({ from: '/book/$bookId' });
  const searchText = urlSearch || '';

  const highlightsData = useHighlightsTabData(book);
  const flashcardsData = useFlashcardsTabData(book);

  const handleTagClick = (newTagId: number | null) => {
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

  const data = activeTab === 'highlights' ? highlightsData : flashcardsData;

  return (
    <MobileNavigation
      book={book}
      onTagClick={handleTagClick}
      selectedTag={data.selectedTagId}
      bookmarks={activeTab === 'highlights' ? book.bookmarks || [] : []}
      allHighlights={activeTab === 'highlights' ? highlightsData.allHighlights : []}
      onBookmarkClick={handleBookmarkClick}
      chapters={data.chapters}
      onChapterClick={handleChapterClick}
      displayTags={data.tags}
    />
  );
};
