import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  getGetBooksApiV1BooksGetQueryKey,
  useDeleteBookApiV1BooksBookIdDelete,
  useUpdateBookApiV1BooksBookIdPost,
} from '@/api/generated/books/books.ts';
import { BookDetails } from '@/api/generated/model';
import { DeleteIcon } from '@/components/Icons.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { Box, Button, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { BookCover } from '@/components/BookCover.tsx';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { TagInput } from '@/components/TagInput.tsx';

interface BookEditFormData {
  tags: string[];
}

interface BookEditModalProps {
  book: BookDetails;
  open: boolean;
  onClose: () => void;
}

export const BookEditModal = ({ book, open, onClose }: BookEditModalProps) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { showSnackbar } = useSnackbar();
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const { control, handleSubmit, reset } = useForm<BookEditFormData>({
    defaultValues: {
      tags: book.tags.map((tag) => tag.name),
    },
  });

  const updateBookMutation = useUpdateBookApiV1BooksBookIdPost({
    mutation: {
      onSuccess: async () => {
        // Invalidate and refetch both the books list and the specific book details
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: getGetBooksApiV1BooksGetQueryKey() }),
          queryClient.invalidateQueries({
            queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(book.id),
          }),
        ]);
        onClose();
      },
      onError: (error) => {
        console.error('Error updating book:', error);
      },
    },
  });

  const deleteBookMutation = useDeleteBookApiV1BooksBookIdDelete({
    mutation: {
      onSuccess: async () => {
        // Refetch the books list query and wait for it to complete
        await queryClient.refetchQueries({
          queryKey: ['/api/v1/books'],
          exact: true,
        });
        // Close modal and navigate to landing page after refetch is complete
        onClose();
        navigate({ to: '/' });
      },
      onError: (error) => {
        console.error('Failed to delete book:', error);
        showSnackbar('Failed to delete book. Please try again.', 'error');
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
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = () => {
    setDeleteConfirmOpen(false);
    deleteBookMutation.mutate({ bookId: book.id });
  };

  const isSaving = updateBookMutation.isPending;
  const isDeleting = deleteBookMutation.isPending;
  const isLoading = isSaving || isDeleting;
  const error = updateBookMutation.error;

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      isLoading={isLoading}
      title="Edit Book"
      footerActions={
        <>
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
        </>
      }
    >
      <Box display="flex" flexDirection="column" gap={3}>
        {/* Book Info Display */}
        <Box
          display="flex"
          flexDirection={{ xs: 'column', sm: 'row' }}
          gap={2}
          alignItems={{ xs: 'center', sm: 'flex-start' }}
          sx={{ mt: 3 }}
        >
          <BookCover
            coverPath={book.cover}
            title={book.title}
            width="120px"
            height="180px"
            objectFit="cover"
          />
          <Box
            flex={1}
            sx={{ textAlign: { xs: 'center', sm: 'left' }, width: { xs: '100%', sm: 'auto' } }}
          >
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

      <ConfirmationDialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Book"
        message={`Are you sure you want to delete "${book.title}"? This will permanently delete the book and all its highlights.`}
        confirmText="Delete"
        confirmColor="error"
        isLoading={isDeleting}
      />
    </CommonDialog>
  );
};
