import { Box, Typography } from '@mui/material';
import { BookmarkBorder as BookmarkIcon } from '@mui/icons-material';
import { Link } from '@tanstack/react-router';
import type { BookWithHighlightCount } from '../../../api/generated/model';
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

          {/* Highlight count overlay */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.75)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 0.5,
              py: 0.5,
              px: 1,
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
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={book.title}
        >
          {truncateText(book.title, 100)}
        </Typography>

        {/* Book author */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            maxWidth: 150,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={book.author || 'Unknown Author'}
        >
          {truncateText(book.author || 'Unknown Author', 100)}
        </Typography>
      </Box>
    </Link>
  );
};
