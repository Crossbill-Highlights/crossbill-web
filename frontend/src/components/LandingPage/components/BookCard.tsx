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
          flexDirection: 'column',
        }}
      >
        <BookCover coverPath={book.cover} title={book.title} height={200} />

        <CardContent>
          <Typography
            variant="h6"
            component="h3"
            gutterBottom
            sx={{ fontWeight: 600, color: 'text.primary', lineHeight: 1.5 }}
          >
            {book.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {book.author || 'Unknown Author'}
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {book.highlight_count} {book.highlight_count === 1 ? 'highlight' : 'highlights'}
            </Typography>
          </Box>
        </CardContent>
      </HoverableCard>
    </Link>
  );
};
