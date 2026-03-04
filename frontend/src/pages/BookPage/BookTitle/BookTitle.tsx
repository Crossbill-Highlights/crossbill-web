import type { BookDetails } from '@/api/generated/model';
import { BookCover } from '@/components/BookCover.tsx';
import { BookTagList } from '@/pages/BookPage/BookTitle/BookTagList.tsx';
import { EditIcon } from '@/theme/Icons.tsx';
import { Box, Button, LinearProgress, Tooltip, Typography } from '@mui/material';
import { useState } from 'react';
import { BookEditModal } from './BookEditModal.tsx';
import { BookStatsStrip } from './BookStatsStrip.tsx';

export interface BookTitleProps {
  book: BookDetails;
}

export const BookTitle = ({ book }: BookTitleProps) => {
  const [editModalOpen, setEditModalOpen] = useState(false);

  const handleEdit = () => {
    setEditModalOpen(true);
  };

  const progress =
    book.reading_position && book.end_position && book.end_position.index > 0
      ? Math.min(100, Math.round((book.reading_position.index / book.end_position.index) * 100))
      : 0;

  return (
    <>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: '280px 1fr 280px' },
          gap: 4,
          alignItems: 'start',
          mb: 2.5,
        }}
      >
        {/* Book Cover */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
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
              sx={{
                boxShadow: 3,
                borderRadius: 1,
                transition: 'box-shadow 0.3s ease, transform 0.3s ease',
              }}
            />
          </Box>
          <Tooltip title={`${progress}% progress`} arrow>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ width: { xs: 160, md: 200 }, mt: 2, borderRadius: 1, height: 6 }}
            />
          </Tooltip>
        </Box>

        {/* Book Info */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: { xs: 'center', lg: 'flex-start' },
            justifyContent: { xs: 'center', lg: 'flex-start' },
            textAlign: { xs: 'center', lg: 'left' },
            width: { xs: '100%', lg: 'auto' },
            position: 'relative',
          }}
        >
          <Typography
            variant="h1"
            component="h1"
            sx={{
              mb: 1,
            }}
          >
            {book.title}
          </Typography>

          <Typography
            variant="h2"
            sx={{
              color: 'primary.main',
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
              justifyContent: { xs: 'center', lg: 'flex-start' },
              alignItems: 'center',
              gap: 1,
              mb: 2,
              width: '100%',
              flexWrap: 'wrap',
            }}
          >
            <Button variant="text" startIcon={<EditIcon />} onClick={handleEdit} size="small">
              Edit
            </Button>
          </Box>

          <BookStatsStrip book={book} />

          <BookTagList tags={book.tags} />
        </Box>
      </Box>

      {/* Edit Modal */}
      <BookEditModal book={book} open={editModalOpen} onClose={() => setEditModalOpen(false)} />
    </>
  );
};
