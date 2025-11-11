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
        mb: 4,
        boxShadow: 3,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'center', sm: 'stretch' },
        }}
      >
        {/* Book Cover - first on mobile, right on desktop */}
        <Box
          sx={{
            flexShrink: 0,
            display: { xs: 'flex', sm: 'block' },
            justifyContent: { xs: 'center', sm: 'initial' },
            width: { xs: '100%', sm: 'auto' },
            pt: { xs: 4, sm: 0 },
            pb: { xs: 2, sm: 0 },
            order: { xs: 0, sm: 1 },
          }}
        >
          <BookCover
            coverPath={book.cover}
            title={book.title}
            height={{ xs: 200, sm: '100%' }}
            width={{ xs: 140, sm: 200 }}
            objectFit="cover"
          />
        </Box>

        {/* Book Info */}
        <Box
          sx={{
            flex: 1,
            p: { xs: 4, sm: 6 },
            pt: { xs: 2, sm: 6 },
            textAlign: { xs: 'center', sm: 'left' },
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
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
