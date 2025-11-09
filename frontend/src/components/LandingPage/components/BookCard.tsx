import MenuBookIcon from '@mui/icons-material/MenuBook';
import { Box, CardContent, Typography } from '@mui/material';
import { Link } from '@tanstack/react-router';
import type { BookWithHighlightCount } from '../../../api/generated/model';
import { HoverableCard } from '../../common/HoverableCard';

export interface BookCardProps {
  book: BookWithHighlightCount;
}

export const BookCard = ({ book }: BookCardProps) => {
  // Get the API base URL for cover images
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const coverUrl = book.cover ? `${apiUrl}${book.cover}` : null;

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
        {/* Book Cover Image */}
        <Box
          sx={{
            width: '100%',
            height: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: coverUrl ? 'transparent' : 'action.hover',
            overflow: 'hidden',
          }}
        >
          {coverUrl ? (
            <img
              src={coverUrl}
              alt={`${book.title} cover`}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
              }}
              onError={(e) => {
                // Fallback to placeholder if image fails to load
                e.currentTarget.style.display = 'none';
                const placeholder = e.currentTarget.nextSibling as HTMLElement;
                if (placeholder) placeholder.style.display = 'flex';
              }}
            />
          ) : null}
          {/* Placeholder icon when no cover is available */}
          <Box
            sx={{
              display: coverUrl ? 'none' : 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              height: '100%',
            }}
          >
            <MenuBookIcon sx={{ fontSize: 80, color: 'text.disabled' }} />
          </Box>
        </Box>

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
