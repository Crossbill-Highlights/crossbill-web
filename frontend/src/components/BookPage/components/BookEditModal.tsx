import { useUpdateBookApiV1BookBookIdPost } from '@/api/generated/books/books.ts';
import { BookWithHighlightCount } from '@/api/generated/model';
import { Close as CloseIcon } from '@mui/icons-material';
import {
  Autocomplete,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { BookCover } from '../../common/BookCover';

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

  const isSaving = updateBookMutation.isPending;
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
            disabled={isSaving}
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
            <Controller
              name="tags"
              control={control}
              render={({ field }) => (
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={field.value}
                  onChange={(_, newValue) => {
                    field.onChange(newValue);
                  }}
                  onBlur={field.onBlur}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Tags"
                      placeholder="Add tags..."
                      helperText="Press Enter to add a tag"
                      disabled={isSaving}
                    />
                  )}
                  slotProps={{
                    chip: {
                      disabled: isSaving,
                    },
                  }}
                  disabled={isSaving}
                />
              )}
            />
          </Box>

          {/* Error Message */}
          {error && (
            <Typography color="error" variant="body2">
              Failed to update book
            </Typography>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={isSaving}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit(onSubmit)}
          variant="contained"
          disabled={isSaving}
          color="primary"
        >
          {isSaving ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
