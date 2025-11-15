import type { BookDetails } from '@/api/generated/model';
import { TagList } from '@/components/BookPage/components/TagList.tsx';
import { BookmarkBorder as BookmarkIcon, Edit as EditIcon } from '@mui/icons-material';
import { Box, Button, Typography } from '@mui/material';
import { useState } from 'react';
import { BookCover } from '../../common/BookCover';
import { BookEditModal } from './BookEditModal';

export interface BookTitleProps {
  book: BookDetails;
  highlightCount: number;
}

export const BookTitle = ({ book, highlightCount }: BookTitleProps) => {
  const [editModalOpen, setEditModalOpen] = useState(false);

  const handleEdit = () => {
    setEditModalOpen(true);
  };

  return (
    <>
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: { xs: 2, md: 3 },
          alignItems: { xs: 'center', md: 'stretch' },
        }}
      >
        {/* Book Cover */}
        <Box
          sx={{
            flexShrink: 0,
            width: { xs: 160, md: 200 },
            height: { xs: 240, md: 280 },
          }}
        >
          <BookCover
            coverPath={book.cover}
            title={book.title}
            height="100%"
            width="100%"
            objectFit="cover"
            sx={{ boxShadow: 3, borderRadius: 1 }}
          />
        </Box>

        {/* Book Info */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: { xs: 'center', md: 'flex-start' },
            justifyContent: { xs: 'center', md: 'flex-start' },
            textAlign: { xs: 'center', md: 'left' },
            width: { xs: '100%', md: 'auto' },
            position: 'relative',
          }}
        >
          {/* Title with Edit Button (Desktop only) */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: { xs: 'center', md: 'flex-start' },
              gap: 1,
              mb: 1,
              width: '100%',
            }}
          >
            <Typography variant="h1" component="h1" sx={{ lineHeight: 1.3 }}>
              {book.title}
            </Typography>
          </Box>

          <Typography
            variant="h2"
            sx={{
              color: 'primary.main',
              fontWeight: 500,
              mb: { xs: 1, md: 2 },
              width: '100%',
            }}
            gutterBottom
          >
            {book.author || 'Unknown Author'}
          </Typography>

          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: { xs: 'center', md: 'flex-start' },
              gap: 1,
              mb: book.tags && book.tags.length > 0 ? 2 : 0,
              width: '100%',
            }}
          >
            <BookmarkIcon sx={{ fontSize: 18, color: 'primary.main' }} />
            <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
              {highlightCount} {highlightCount === 1 ? 'highlight' : 'highlights'}
            </Typography>
            <Button variant="text" startIcon={<EditIcon />} onClick={handleEdit} size="small">
              Edit
            </Button>
          </Box>

          <TagList tags={book.tags} />
        </Box>
      </Box>

      {/* Edit Modal */}
      <BookEditModal
        book={{
          id: book.id,
          title: book.title,
          author: book.author,
          isbn: book.isbn,
          cover: book.cover,
          highlight_count: highlightCount,
          tags: book.tags || [],
          created_at: book.created_at,
          updated_at: book.updated_at,
        }}
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
      />
    </>
  );
};
