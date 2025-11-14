import type { BookWithHighlightCount } from '@/api/generated/model';
import { theme } from '@/theme/theme.ts';
import { BookmarkBorder as BookmarkIcon } from '@mui/icons-material';
import { Box, Typography } from '@mui/material';
import { Link } from '@tanstack/react-router';
import { BookCover } from '../../common/BookCover';

export interface BookCardProps {
  book: BookWithHighlightCount;
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

export const BookCard = ({ book }: BookCardProps) => {
  return (
    <Link
      to="/book/$bookId"
      params={{ bookId: String(book.id) }}
      style={{ textDecoration: 'none', color: 'inherit', display: 'inline-block' }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          width: 'fit-content',
          transition: 'transform 0.2s',
          '&:hover': {
            transform: 'translateY(-4px)',
          },
        }}
      >
        {/* Book cover with highlight count overlay */}
        <Box sx={{ position: 'relative', width: 'fit-content' }}>
          <BookCover
            coverPath={book.cover}
            title={book.title}
            width={150}
            height={220}
            objectFit="cover"
          />

          {/* Highlight count chip */}
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              backgroundColor: theme.palette.primary.main,
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              py: 0.5,
              px: 1,
              borderRadius: 2,
            }}
          >
            <BookmarkIcon sx={{ fontSize: 16, color: 'white' }} />
            <Typography
              variant="caption"
              sx={{
                color: 'white',
                fontWeight: 500,
              }}
            >
              {book.highlight_count}
            </Typography>
          </Box>
        </Box>

        {/* Book title */}
        <Typography
          variant="body1"
          component="h3"
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            mt: 1,
            maxWidth: 150,
          }}
          title={book.title}
        >
          {truncateText(book.title, 50)}
        </Typography>

        {/* Book author */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            maxWidth: 150,
          }}
          title={book.author || 'Unknown Author'}
        >
          {truncateText(book.author || 'Unknown Author', 30)}
        </Typography>
      </Box>
    </Link>
  );
};
