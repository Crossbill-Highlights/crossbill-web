import {
  getGetRecentlyViewedBooksApiV1BooksRecentlyViewedGetQueryKey,
  useGetBookDetailsApiV1BooksBookIdGet,
} from '@/api/generated/books/books';
import type { BookDetails } from '@/api/generated/model';
import { BookTitle } from '@/components/BookPage/BookTitle/BookTitle.tsx';
import { FlashcardsTab } from '@/components/BookPage/FlashcardsTab/FlashcardsTab.tsx';
import { HighlightsTab } from '@/components/BookPage/HighlightsTab/HighlightsTab.tsx';
import { FadeInOut } from '@/components/common/animations/FadeInOut.tsx';
import { scrollToElementWithHighlight } from '@/components/common/animations/scrollUtils';
import { FlashcardsIcon, HighlightsIcon } from '@/components/common/Icons.tsx';
import { ThreeColumnLayout } from '@/components/layout/Layouts.tsx';
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
import { useCallback, useEffect, useMemo } from 'react';
import { ScrollToTopButton } from '../common/ScrollToTopButton';
import { Spinner } from '../common/Spinner';

type TabValue = 'highlights' | 'flashcards';

const BookTabs = ({
  activeTab,
  handleTabChange,
  book,
}: {
  activeTab: TabValue;
  handleTabChange: (_event: React.SyntheticEvent, newValue: TabValue) => void;
  book: BookDetails;
}) => {
  const totalHighlights = useMemo(() => {
    return book.chapters?.reduce((sum, chapter) => sum + (chapter.highlights?.length || 0), 0) || 0;
  }, [book.chapters]);

  const totalFlashcards = useMemo(() => {
    if (!book.chapters) return 0;
    return flatMap(book.chapters, (chapter) =>
      flatMap(chapter.highlights || [], (highlight) => highlight.flashcards || [])
    ).length;
  }, [book.chapters]);

  return (
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
};

export const BookPage = () => {
  const { bookId } = useParams({ from: '/book/$bookId' });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BooksBookIdGet(Number(bookId));

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

  return <BookPageContent book={book} />;
};

interface BookPageContentProps {
  book: BookDetails;
}

const BookPageContent = ({ book }: BookPageContentProps) => {
  const { tab, search: urlSearch } = useSearch({ from: '/book/$bookId' });

  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  const navigate = useNavigate({ from: '/book/$bookId' });
  const activeTab: TabValue = tab || 'highlights';

  // Update recently viewed on mount
  useEffect(() => {
    void queryClient.invalidateQueries({
      queryKey: getGetRecentlyViewedBooksApiV1BooksRecentlyViewedGetQueryKey(),
    });
  }, []);

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

  const handleSearch = useCallback(
    (value: string) => {
      navigate({
        search: (prev) => ({
          ...prev,
          search: value || undefined,
        }),
        replace: true,
      });
    },
    [navigate]
  );

  const handleTagClick = useCallback(
    (newTagId: number | null) => {
      navigate({
        search: (prev) => ({
          ...prev,
          tagId: newTagId || undefined,
        }),
        replace: true,
      });
    },
    [navigate]
  );

  const handleBookmarkClick = useCallback(
    (highlightId: number) => {
      if (urlSearch) {
        navigate({
          search: (prev) => ({
            ...prev,
            search: undefined,
          }),
          replace: true,
        });
      }
      scrollToElementWithHighlight(`highlight-${highlightId}`, { behavior: 'smooth' });
    },
    [navigate, urlSearch]
  );

  const handleChapterClick = useCallback(
    (chapterId: number) => {
      if (urlSearch) {
        navigate({
          search: (prev) => ({
            ...prev,
            search: undefined,
          }),
          replace: true,
        });
      }
      scrollToElementWithHighlight(`chapter-${chapterId}`, { behavior: 'smooth', block: 'start' });
    },
    [navigate, urlSearch]
  );

  return (
    <Container sx={{ minHeight: '100vh' }} maxWidth="xl">
      <ScrollToTopButton />
      <FadeInOut ekey={'book-title'}>
        {isDesktop ? (
          <Box sx={{ pt: 4 }}>
            <BookTitle book={book} />
            <ThreeColumnLayout>
              <div></div> {/* Empty left column for spacing */}
              <BookTabs activeTab={activeTab} handleTabChange={handleTabChange} book={book} />
            </ThreeColumnLayout>
          </Box>
        ) : (
          <Box sx={{ pt: 8, maxWidth: '800px', mx: 'auto' }}>
            <BookTitle book={book} />
            <BookTabs activeTab={activeTab} handleTabChange={handleTabChange} book={book} />
          </Box>
        )}
        {activeTab === 'highlights' ? (
          <HighlightsTab
            book={book}
            isDesktop={isDesktop}
            onSearch={handleSearch}
            onTagClick={handleTagClick}
            onBookmarkClick={handleBookmarkClick}
            onChapterClick={handleChapterClick}
          />
        ) : (
          <FlashcardsTab
            book={book}
            isDesktop={isDesktop}
            onSearch={handleSearch}
            onTagClick={handleTagClick}
            onChapterClick={handleChapterClick}
          />
        )}
      </FadeInOut>
    </Container>
  );
};
