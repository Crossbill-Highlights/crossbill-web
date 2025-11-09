import { Alert, Box, Card, CardContent, Container, Typography } from '@mui/material';
import { useParams } from '@tanstack/react-router';
import { useGetBookDetailsApiV1BookBookIdGet } from '../../api/generated/books/books';
import { Spinner } from '../common/Spinner';

export const BookPage = () => {
  const { bookId } = useParams({ from: '/book/$bookId' });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BookBookIdGet(Number(bookId));

  if (isLoading) {
    return (
      <Container maxWidth="lg">
        <Spinner />
      </Container>
    );
  }

  if (isError || !book) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          <Alert severity="error">Failed to load book details. Please try again later.</Alert>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 6 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          {book.title}
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          {book.author || 'Unknown Author'}
        </Typography>
      </Box>

      <Box sx={{ mb: 4 }}>
        {book.chapters && book.chapters.length === 0 && (
          <Typography variant="body1" color="text.secondary">
            No chapters found for this book.
          </Typography>
        )}

        {book.chapters && book.chapters.length > 0 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {book.chapters.map((chapter) => (
              <Box key={chapter.id}>
                <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 2 }}>
                  {chapter.name}
                </Typography>

                {chapter.highlights && chapter.highlights.length > 0 ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {chapter.highlights.map((highlight) => (
                      <Card
                        key={highlight.id}
                        sx={{
                          transition: 'box-shadow 0.2s',
                          '&:hover': {
                            boxShadow: 2,
                          },
                        }}
                      >
                        <CardContent>
                          <Typography
                            variant="body1"
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: 3,
                              WebkitBoxOrient: 'vertical',
                              mb: 1,
                            }}
                          >
                            {highlight.text}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(highlight.datetime).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })}
                            {highlight.page && ` • Page ${highlight.page}`}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No highlights found in this chapter.
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </Container>
  );
};
