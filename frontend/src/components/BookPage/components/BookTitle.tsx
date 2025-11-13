import {
  BookmarkBorder as BookmarkIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { Box, Card, IconButton, ListItemIcon, Menu, MenuItem, Typography } from '@mui/material';
import { useNavigate } from '@tanstack/react-router';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useDeleteBookApiV1BookBookIdDelete } from '../../../api/generated/books/books';
import type { BookDetails } from '../../../api/generated/model';
import { BookCover } from '../../common/BookCover';
import { BookEditModal } from './BookEditModal';

export interface BookTitleProps {
  book: BookDetails;
  highlightCount: number;
}

export const BookTitle = ({ book, highlightCount }: BookTitleProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const menuOpen = Boolean(anchorEl);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const deleteBookMutation = useDeleteBookApiV1BookBookIdDelete({
    mutation: {
      onSuccess: () => {
        // Immediately refetch the books list query to refresh the UI
        queryClient.refetchQueries({
          queryKey: ['/api/v1/highlights/books'],
          exact: true,
        });
        // Navigate to landing page after successful delete
        navigate({ to: '/' });
      },
      onError: (error) => {
        console.error('Failed to delete book:', error);
        alert('Failed to delete book. Please try again.');
      },
    },
  });

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = (event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    setAnchorEl(null);
  };

  const handleEdit = (event: React.MouseEvent) => {
    event.stopPropagation();
    handleMenuClose();
    setEditModalOpen(true);
  };

  const handleDelete = (event: React.MouseEvent) => {
    event.stopPropagation();
    handleMenuClose();

    if (
      confirm(
        `Are you sure you want to delete "${book.title}"? This will permanently delete the book and all its highlights.`
      )
    ) {
      deleteBookMutation.mutate({ bookId: book.id });
    }
  };

  return (
    <>
      <Box sx={{ mb: 4, display: 'flex', gap: 3, alignItems: 'stretch' }}>
        {/* Book Cover - Outside card, on the left */}
        <Box sx={{ flexShrink: 0 }}>
          <BookCover
            coverPath={book.cover}
            title={book.title}
            height={280}
            width={200}
            objectFit="cover"
            sx={{ boxShadow: 3, borderRadius: 1 }}
          />
        </Box>

        {/* Book Info Card */}
        <Card
          sx={{
            flex: 1,
            boxShadow: 3,
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Menu Button - Bottom right corner */}
          <IconButton
            size="small"
            onClick={handleMenuOpen}
            sx={{
              position: 'absolute',
              bottom: 8,
              right: 8,
              zIndex: 1,
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            <MoreVertIcon fontSize="small" />
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={menuOpen}
            onClose={(event) => handleMenuClose(event as React.MouseEvent)}
            onClick={(event) => event.stopPropagation()}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
          >
            <MenuItem onClick={handleEdit}>
              <ListItemIcon>
                <EditIcon fontSize="small" />
              </ListItemIcon>
              Edit
            </MenuItem>
            <MenuItem onClick={handleDelete}>
              <ListItemIcon>
                <DeleteIcon fontSize="small" />
              </ListItemIcon>
              Delete
            </MenuItem>
          </Menu>

          {/* Book Info Content */}
          <Box
            sx={{
              p: { xs: 4, sm: 6 },
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              flex: 1,
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
                gap: 1,
              }}
            >
              <BookmarkIcon sx={{ fontSize: 18, color: 'primary.main' }} />
              <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
                {highlightCount} {highlightCount === 1 ? 'highlight' : 'highlights'}
              </Typography>
            </Box>
          </Box>
        </Card>
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
          tags: [], // TODO: Add tags to BookDetails type
          created_at: book.created_at,
          updated_at: book.updated_at,
        }}
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
      />
    </>
  );
};
