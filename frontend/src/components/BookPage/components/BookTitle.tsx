import { BookmarkBorder as BookmarkIcon } from '@mui/icons-material';
import { Box, Card, Typography } from '@mui/material';
import type { BookDetails } from '../../../api/generated/model';
import { BookCover } from '../../common/BookCover';

export interface BookTitleProps {
  book: BookDetails;
  highlightCount: number;
}

export const BookTitle = ({ book, highlightCount }: BookTitleProps) => {
  return (
    <Card
      sx={{
        p: { xs: 4, sm: 6 },
        mb: 4,
        boxShadow: 3,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'center', sm: 'start' },
          justifyContent: 'space-between',
          gap: { xs: 3, sm: 0 },
        }}
      >
        {/* Book Cover - displayed first on mobile */}
        <Box
          sx={{
            order: { xs: -1, sm: 1 },
            flexShrink: 0,
            ml: { xs: 0, sm: 2 },
          }}
        >
          <BookCover
            coverPath={book.cover}
            title={book.title}
            height={200}
            width={{ xs: 140, sm: 128 }}
          />
        </Box>

        {/* Book Info */}
        <Box
          sx={{
            flex: 1,
            textAlign: { xs: 'center', sm: 'left' },
            order: { xs: 1, sm: 0 },
          }}
        >
          <Typography variant="h1" component="h1" gutterBottom sx={{ lineHeight: 1.3, mb: 1 }}>
            {book.title}
          </Typography>
          <Typography
            variant="h2"
            sx={{ color: 'primary.main', fontWeight: 500, mb: 2 }}
            gutterBottom
          >
            {book.author || 'Unknown Author'}
          </Typography>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: { xs: 'center', sm: 'flex-start' },
              gap: 1,
            }}
          >
            <BookmarkIcon sx={{ fontSize: 18, color: 'primary.main' }} />
            <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
              {highlightCount} {highlightCount === 1 ? 'highlight' : 'highlights'}
            </Typography>
          </Box>
        </Box>
      </Box>
    </Card>
  );
};
