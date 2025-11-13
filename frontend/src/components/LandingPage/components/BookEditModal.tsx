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
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { BookCover } from '../../common/BookCover';

// Type definitions (will be replaced by generated types once API is regenerated)
interface Tag {
  id: number;
  name: string;
}

interface BookWithHighlightCount {
  id: number;
  title: string;
  author: string | null;
  isbn: string | null;
  cover: string | null;
  highlight_count: number;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

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
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { control, handleSubmit, reset } = useForm<BookEditFormData>({
    defaultValues: {
      tags: book.tags.map((tag) => tag.name),
    },
  });

  // Reset form when modal opens with new book data
  const handleModalOpen = () => {
    reset({
      tags: book.tags.map((tag) => tag.name),
    });
    setError(null);
  };

  const onSubmit = async (data: BookEditFormData) => {
    setIsSaving(true);
    setError(null);

    try {
      // Make API call to update book
      const response = await fetch(`/api/v1/book/${book.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tags: data.tags,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update book: ${response.statusText}`);
      }

      // Refetch the books list to update the UI
      await queryClient.refetchQueries({
        queryKey: ['/api/v1/highlights/books'],
        exact: true,
      });

      onClose();
    } catch (err) {
      console.error('Error updating book:', err);
      setError(err instanceof Error ? err.message : 'Failed to update book');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      TransitionProps={{
        onEntered: handleModalOpen,
      }}
    >
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
              {error}
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
