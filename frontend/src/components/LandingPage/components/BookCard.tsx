import { Box, CardContent, Typography } from '@mui/material';
import { Link } from '@tanstack/react-router';
import type { BookWithHighlightCount } from '../../../api/generated/model';
import { BookCover } from '../../common/BookCover';
import { HoverableCard } from '../../common/HoverableCard';

export interface BookCardProps {
  book: BookWithHighlightCount;
}

export const BookCard = ({ book }: BookCardProps) => {
  return (
    <Link
      to="/book/$bookId"
      params={{ bookId: String(book.id) }}
      style={{ textDecoration: 'none', color: 'inherit' }}
    >
      <HoverableCard
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'row',
          position: 'relative',
          minHeight: 180,
        }}
      >
        <BookCover
          coverPath={book.cover}
          title={book.title}
          width="35%"
          height="100%"
          objectFit="cover"
          sx={{ flexShrink: 0 }}
        />

        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', paddingRight: 6 }}>
          <Typography
            variant="h6"
            component="h3"
            gutterBottom
            sx={{ fontWeight: 600, color: 'text.primary', lineHeight: 1.5 }}
          >
            {book.title}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            gutterBottom
            sx={{
              width: { xs: '120px', sm: '200px' },
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {book.author || 'Unknown Author'}
          </Typography>
          <Box sx={{ mt: 'auto' }}>
            <Typography variant="body2" color="text.secondary">
              {book.highlight_count} {book.highlight_count === 1 ? 'highlight' : 'highlights'}
            </Typography>
          </Box>
        </CardContent>
      </HoverableCard>
    </Link>
  );
};
