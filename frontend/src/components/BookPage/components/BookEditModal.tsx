import { Close as CloseIcon } from '@mui/icons-material';
import {
  Autocomplete,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import {
  BookWithHighlightCount,
  useUpdateBookApiV1BookBookIdPost,
} from '../../../api/book-update';
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
  const { control, handleSubmit, reset } = useForm<BookEditFormData>({
    defaultValues: {
      tags: book.tags.map((tag) => tag.name),
    },
  });

  const updateBookMutation = useUpdateBookApiV1BookBookIdPost({
    mutation: {
      onSuccess: () => {
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
        tags: book.tags.map((tag) => tag.name),
      });
      updateBookMutation.reset(); // Reset mutation state
    }
  }, [open, book.tags, reset, updateBookMutation]);

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
                  {...field}
                  multiple
                  freeSolo
                  options={[]}
                  value={field.value}
                  onChange={(_, newValue) => {
                    field.onChange(newValue);
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        label={option}
                        {...getTagProps({ index })}
                        key={option}
                        disabled={isSaving}
                      />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Tags"
                      placeholder="Add tags..."
                      helperText="Press Enter to add a tag"
                      disabled={isSaving}
                    />
                  )}
                  disabled={isSaving}
                />
              )}
            />
          </Box>

          {/* Error Message */}
          {error && (
            <Typography color="error" variant="body2">
              {error instanceof Error ? error.message : 'Failed to update book'}
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
