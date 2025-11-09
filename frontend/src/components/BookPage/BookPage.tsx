import {
  BookmarkBorder as BookmarkIcon,
  CalendarMonth as CalendarIcon,
  ChevronRight as ChevronRightIcon,
  FormatQuote as QuoteIcon,
} from '@mui/icons-material';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Collapse,
  Container,
  IconButton,
  Typography,
} from '@mui/material';
import { useParams } from '@tanstack/react-router';
import { useState } from 'react';
import { useGetBookDetailsApiV1BookBookIdGet } from '../../api/generated/books/books';
import { HoverableCard } from '../common/HoverableCard';
import { SectionTitle } from '../common/SectionTitle';
import { Spinner } from '../common/Spinner';

export const BookPage = () => {
  const { bookId } = useParams({ from: '/book/$bookId' });
  const { data: book, isLoading, isError } = useGetBookDetailsApiV1BookBookIdGet(Number(bookId));
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  const toggleCard = (id: number) => {
    setExpandedCard(expandedCard === id ? null : id);
  };

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
            <Box
              sx={(theme) => ({
                width: { xs: 80, sm: 96 },
                height: { xs: 106, sm: 128 },
                background: `linear-gradient(135deg, ${theme.palette.primary.light} 0%, ${theme.palette.primary.dark} 100%)`,
                borderRadius: 2,
                boxShadow: 2,
                flexShrink: 0,
                ml: 2,
              })}
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
                    {chapter.highlights.map((highlight) => {
                      const isExpanded = expandedCard === highlight.id;
                      const previewText =
                        highlight.text.length > 120
                          ? highlight.text.substring(0, 120) + '...'
                          : highlight.text;

                      return (
                        <HoverableCard
                          key={highlight.id}
                          sx={{
                            overflow: 'visible',
                          }}
                        >
                          <CardContent
                            onClick={() => toggleCard(highlight.id)}
                            sx={{
                              '&:last-child': { pb: 3 },
                            }}
                          >
                            <Box
                              sx={{
                                display: 'flex',
                                alignItems: 'start',
                                justifyContent: 'space-between',
                                gap: 2,
                              }}
                            >
                              <Box sx={{ flex: 1, minWidth: 0 }}>
                                {/* Quote Icon and Text */}
                                <Box sx={{ display: 'flex', alignItems: 'start', gap: 1.5, mb: 2 }}>
                                  <QuoteIcon
                                    sx={{
                                      fontSize: 18,
                                      color: 'primary.main',
                                      flexShrink: 0,
                                      mt: 0.3,
                                    }}
                                  />
                                  <Typography
                                    variant="body1"
                                    sx={{
                                      fontWeight: 600,
                                      color: 'text.primary',
                                      lineHeight: 1.5,
                                    }}
                                  >
                                    {previewText}
                                  </Typography>
                                </Box>

                                {/* Expanded Full Text */}
                                <Collapse in={isExpanded}>
                                  <Typography
                                    variant="body1"
                                    sx={{
                                      color: 'secondary.dark',
                                      lineHeight: 1.6,
                                      mb: 2,
                                      pl: 4.5,
                                    }}
                                  >
                                    {highlight.text.length > 120 && highlight.text.substring(120)}
                                  </Typography>
                                </Collapse>

                                {/* Date and Page */}
                                <Box
                                  sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1,
                                    pl: 4.5,
                                  }}
                                >
                                  <CalendarIcon
                                    sx={(theme) => ({
                                      fontSize: 14,
                                      color:
                                        theme.palette.mode === 'light'
                                          ? `rgba(${parseInt(theme.palette.secondary.main.slice(1, 3), 16)}, ${parseInt(theme.palette.secondary.main.slice(3, 5), 16)}, ${parseInt(theme.palette.secondary.main.slice(5, 7), 16)}, 0.7)`
                                          : 'secondary.light',
                                    })}
                                  />
                                  <Typography
                                    variant="caption"
                                    sx={(theme) => ({
                                      color:
                                        theme.palette.mode === 'light'
                                          ? `rgba(${parseInt(theme.palette.secondary.main.slice(1, 3), 16)}, ${parseInt(theme.palette.secondary.main.slice(3, 5), 16)}, ${parseInt(theme.palette.secondary.main.slice(5, 7), 16)}, 0.9)`
                                          : 'secondary.light',
                                    })}
                                  >
                                    {new Date(highlight.datetime).toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'long',
                                      day: 'numeric',
                                    })}
                                    {highlight.page && ` • Page ${highlight.page}`}
                                  </Typography>
                                </Box>
                              </Box>

                              {/* Expand/Collapse Icon */}
                              <IconButton
                                size="small"
                                sx={{
                                  color: 'primary.main',
                                  transition: 'transform 0.2s',
                                  transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                                  flexShrink: 0,
                                }}
                              >
                                <ChevronRightIcon />
                              </IconButton>
                            </Box>
                          </CardContent>
                        </HoverableCard>
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
      </Container>
    </Box>
  );
};
