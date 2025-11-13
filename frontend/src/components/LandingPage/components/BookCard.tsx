import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import {
  Box,
  CardContent,
  IconButton,
  ListItemIcon,
  Menu,
  MenuItem,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { useDeleteBookApiV1BookBookIdDelete } from '../../../api/generated/books/books';
import type { BookWithHighlightCount } from '../../../api/generated/model';
import { BookCover } from '../../common/BookCover';
import { HoverableCard } from '../../common/HoverableCard';
import { BookEditModal } from './BookEditModal';

export interface BookCardProps {
  book: BookWithHighlightCount;
}

export const BookCard = ({ book }: BookCardProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const menuOpen = Boolean(anchorEl);
  const queryClient = useQueryClient();

  const deleteBookMutation = useDeleteBookApiV1BookBookIdDelete({
    mutation: {
      onSuccess: () => {
        // Immediately refetch the books list query to refresh the UI
        queryClient.refetchQueries({
          queryKey: ['/api/v1/highlights/books'],
          exact: true,
        });
      },
      onError: (error) => {
        console.error('Failed to delete book:', error);
        alert('Failed to delete book. Please try again.');
      },
    },
  });

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = (event?: React.MouseEvent) => {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    setAnchorEl(null);
  };

  const handleEdit = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    handleMenuClose();
    setEditModalOpen(true);
  };

  const handleDelete = (event: React.MouseEvent) => {
    event.preventDefault();
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
          {/* Menu Button */}
          <IconButton
            size="small"
            onClick={handleMenuOpen}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              zIndex: 1,
              '&:hover': {
                bgcolor: 'background.paper',
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
              vertical: 'bottom',
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

      {/* Edit Modal - rendered outside Link to prevent navigation on modal clicks */}
      <BookEditModal book={book} open={editModalOpen} onClose={() => setEditModalOpen(false)} />
    </>
  );
};
