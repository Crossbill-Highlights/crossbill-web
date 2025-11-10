import { BookmarkBorder as BookmarkIcon } from '@mui/icons-material';
import { Alert, Box, Card, Container, Typography } from '@mui/material';
import { useParams } from '@tanstack/react-router';
import { useGetBookDetailsApiV1BookBookIdGet } from '../../api/generated/books/books';
import { BookCover } from '../common/BookCover';
import { SectionTitle } from '../common/SectionTitle';
import { Spinner } from '../common/Spinner';
import { HighlightCard } from './components/HighlightCard';

export const BookPage = () => {
  const { bookId } = useParams({ from: '/book/$bookId' });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BookBookIdGet(Number(bookId));

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

  return (
    <Box
      sx={{
        minHeight: '100vh',
      }}
    >
      <Container maxWidth="lg" sx={{ px: { xs: 2, sm: 3 }, py: 4 }}>
        {/* Book Info Card */}
        <Card
          sx={{
            p: { xs: 4, sm: 6 },
            mb: 4,
            boxShadow: 3,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between' }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h1" component="h1" gutterBottom sx={{ lineHeight: 1.3, mb: 1 }}>
                {book.title}
              </Typography>
              <Typography
                variant="h2"
                sx={{ color: 'primary.dark', fontWeight: 500, mb: 2 }}
                gutterBottom
              >
                {book.author || 'Unknown Author'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BookmarkIcon sx={{ fontSize: 18, color: 'primary.main' }} />
                <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
                  {totalHighlights} {totalHighlights === 1 ? 'highlight' : 'highlights'}
                </Typography>
              </Box>
            </Box>
            {/* Book Cover */}
            <BookCover
              coverPath={book.cover}
              title={book.title}
              width={{ xs: 80, sm: 96 }}
              height={{ xs: 106, sm: 128 }}
              objectFit="cover"
              gradientPlaceholder
              sx={{ boxShadow: 2, flexShrink: 0, ml: 2 }}
            />
          </Box>
        </Card>

        {/* Highlights by Chapter */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {book.chapters && book.chapters.length === 0 && (
            <Typography variant="body1" color="text.secondary">
              No chapters found for this book.
            </Typography>
          )}

          {book.chapters &&
            book.chapters.length > 0 &&
            book.chapters.map((chapter) => (
              <Box key={chapter.id}>
                {/* Chapter Header */}
                <SectionTitle showDivider>{chapter.name}</SectionTitle>

                {/* Highlights in this chapter */}
                {chapter.highlights && chapter.highlights.length > 0 ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    {chapter.highlights.map((highlight) => (
                      <HighlightCard key={highlight.id} highlight={highlight} />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ pl: 0.5 }}>
                    No highlights found in this chapter.
                  </Typography>
                )}
              </Box>
            ))}
        </Box>
      </Container>
    </Box>
  );
};
