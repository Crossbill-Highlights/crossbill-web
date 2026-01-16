import type { BookDetails } from '@/api/generated/model';
import { BookCover } from '@/components/BookCover.tsx';
import { BookTagList } from '@/pages/BookPage/BookTitle/BookTagList.tsx';
import { EditIcon, ExpandLessIcon, ExpandMoreIcon } from '@/theme/Icons.tsx';
import { Box, Button, Typography } from '@mui/material';
import DOMPurify from 'dompurify';
import { useMemo, useState } from 'react';
import { BookEditModal } from './BookEditModal.tsx';

// Strip HTML tags from description for plain text preview
const stripHtml = (html: string): string => {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent || '';
};

// Sanitize HTML for safe rendering
const sanitizeHtml = (html: string): string => {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'div', 'span'],
    ALLOWED_ATTR: [],
  });
};

export interface BookTitleProps {
  book: BookDetails;
}

export const BookTitle = ({ book }: BookTitleProps) => {
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);

  const handleEdit = () => {
    setEditModalOpen(true);
  };

  // Process description - create plain text for preview and sanitized HTML for expanded view
  const { plainDescription, sanitizedHtml, isLongDescription } = useMemo(() => {
    if (!book.description) {
      return { plainDescription: null, sanitizedHtml: null, isLongDescription: false };
    }
    const plain = stripHtml(book.description);
    const sanitized = sanitizeHtml(book.description);
    return {
      plainDescription: plain,
      sanitizedHtml: sanitized,
      isLongDescription: plain.length > 300,
    };
  }, [book.description]);

  const truncatedDescription =
    isLongDescription && !descriptionExpanded ? plainDescription!.slice(0, 300) + '...' : null;

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
            justifyContent: 'center',
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

          {sanitizedHtml && (
            <Box sx={{ mb: 2, width: '100%' }}>
              {/* Show truncated plain text when collapsed, or full HTML when expanded */}
              {truncatedDescription ? (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                    lineHeight: 1.6,
                  }}
                >
                  {truncatedDescription}
                </Typography>
              ) : (
                <Box
                  sx={{
                    color: 'text.secondary',
                    lineHeight: 1.6,
                    fontSize: '0.875rem',
                    '& p': { my: 1 },
                    '& p:first-of-type': { mt: 0 },
                    '& p:last-of-type': { mb: 0 },
                    '& ul, & ol': { pl: 2, my: 1 },
                    '& li': { mb: 0.5 },
                  }}
                  dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
                />
              )}
              {isLongDescription && (
                <Button
                  size="small"
                  onClick={() => setDescriptionExpanded(!descriptionExpanded)}
                  endIcon={descriptionExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  sx={{ mt: 0.5, p: 0, minWidth: 'auto' }}
                >
                  {descriptionExpanded ? 'Show less' : 'Show more'}
                </Button>
              )}
            </Box>
          )}

          <Box
            sx={{
              display: 'flex',
              justifyContent: { xs: 'center', lg: 'flex-start' },
              alignItems: 'center',
              gap: 1,
              mb: book.tags.length > 0 ? 2 : 0,
              width: '100%',
              flexWrap: 'wrap',
            }}
          >
            <Button variant="text" startIcon={<EditIcon />} onClick={handleEdit} size="small">
              Edit
            </Button>
          </Box>

          <BookTagList tags={book.tags} />
        </Box>
      </Box>

      {/* Edit Modal */}
      <BookEditModal book={book} open={editModalOpen} onClose={() => setEditModalOpen(false)} />
    </>
  );
};
