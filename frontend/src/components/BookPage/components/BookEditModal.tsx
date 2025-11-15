import {
  useDeleteBookApiV1BookBookIdDelete,
  useUpdateBookApiV1BookBookIdPost,
} from '@/api/generated/books/books.ts';
import { BookWithHighlightCount } from '@/api/generated/model';
import { Close as CloseIcon, Delete as DeleteIcon } from '@mui/icons-material';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { BookCover } from '../../common/BookCover';
import { TagInput } from '../../common/TagInput';

interface BookEditFormData {
  tags: string[];
}

interface BookEditModalProps {
  book: BookWithHighlightCount;
  open: boolean;
  onClose: () => void;
}

export const BookEditModal = ({ book, open, onClose }: BookEditModalProps) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { control, handleSubmit, reset } = useForm<BookEditFormData>({
    defaultValues: {
      tags: book.tags?.map((tag) => tag.name) || [],
    },
  });

  const updateBookMutation = useUpdateBookApiV1BookBookIdPost({
    mutation: {
      onSuccess: async () => {
        // Invalidate and refetch both the books list and the specific book details
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ['/api/v1/highlights/books'] }),
          queryClient.invalidateQueries({ queryKey: [`/api/v1/book/${book.id}`] }),
        ]);
        onClose();
      },
      onError: (error) => {
        console.error('Error updating book:', error);
      },
    },
  });

  const deleteBookMutation = useDeleteBookApiV1BookBookIdDelete({
    mutation: {
      onSuccess: async () => {
        // Refetch the books list query and wait for it to complete
        await queryClient.refetchQueries({
          queryKey: ['/api/v1/highlights/books'],
          exact: true,
        });
        // Close modal and navigate to landing page after refetch is complete
        onClose();
        navigate({ to: '/' });
      },
      onError: (error) => {
        console.error('Failed to delete book:', error);
        alert('Failed to delete book. Please try again.');
      },
    },
  });

  // Reset form when modal opens - always use the latest book data
  useEffect(() => {
    if (open) {
      reset({
        tags: book.tags?.map((tag) => tag.name) || [],
      });
      updateBookMutation.reset(); // Reset mutation state
    }
    // Only run when modal opens - reset and updateBookMutation are stable/not needed in deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const onSubmit = (data: BookEditFormData) => {
    updateBookMutation.mutate({
      bookId: book.id,
      data: {
        tags: data.tags,
      },
    });
  };

  const handleDelete = () => {
    if (
      confirm(
        `Are you sure you want to delete "${book.title}"? This will permanently delete the book and all its highlights.`
      )
    ) {
      deleteBookMutation.mutate({ bookId: book.id });
    }
  };

  const isSaving = updateBookMutation.isPending;
  const isDeleting = deleteBookMutation.isPending;
  const isLoading = isSaving || isDeleting;
  const error = updateBookMutation.error;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          Edit Book
          <IconButton
            edge="end"
            color="inherit"
            onClick={onClose}
            aria-label="close"
            disabled={isLoading}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box display="flex" flexDirection="column" gap={3}>
          {/* Book Info Display */}
          <Box display="flex" gap={2}>
            <BookCover
              coverPath={book.cover}
              title={book.title}
              width="120px"
              height="180px"
              objectFit="cover"
            />
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                {book.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {book.author || 'Unknown Author'}
              </Typography>
              {book.isbn && (
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  ISBN: {book.isbn}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                {book.highlight_count} {book.highlight_count === 1 ? 'highlight' : 'highlights'}
              </Typography>
            </Box>
          </Box>

          {/* Editable Tags Field */}
          <Box>
            <TagInput control={control} name="tags" disabled={isLoading} />
          </Box>

          {/* Error Message */}
          {error && (
            <Typography color="error" variant="body2">
              Failed to update book
            </Typography>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ justifyContent: 'space-between' }}>
        <Button
          onClick={handleDelete}
          color="error"
          startIcon={<DeleteIcon />}
          disabled={isLoading}
        >
          {isDeleting ? 'Deleting...' : 'Delete'}
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit(onSubmit)}
            variant="contained"
            disabled={isLoading}
            color="primary"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
};
