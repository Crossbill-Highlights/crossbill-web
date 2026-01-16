import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete } from '@/api/generated/flashcards/flashcards.ts';
import { FlashcardWithContext } from '@/components/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { Collapsable } from '@/components/common/animations/Collapsable.tsx';
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog.tsx';
import { DeleteIcon, EditIcon } from '@/components/common/Icons.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { Box, Card, CardActionArea, IconButton, Tooltip, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

export interface FlashcardCardProps {
  flashcard: FlashcardWithContext;
  bookId: number;
  onEdit: () => void;
  component?: React.ElementType;
}

export const FlashcardListCard = ({ flashcard, bookId, onEdit }: FlashcardCardProps) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const queryClient = useQueryClient();
  const { showSnackbar } = useSnackbar();

  const deleteMutation = useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to delete flashcard:', error);
        showSnackbar('Failed to delete flashcard. Please try again.', 'error');
      },
    },
  });

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteConfirmOpen(true);
  };

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit();
  };

  const handleConfirmDelete = async () => {
    setDeleteConfirmOpen(false);
    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync({ flashcardId: flashcard.id });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <li key={flashcard.id}>
      <Card
        sx={{
          p: 1.5,
          borderRadius: 1,
          bgcolor: 'action.hover',
          position: 'relative',
          border: 0,
          boxShadow: 0,
        }}
      >
        <CardActionArea onClick={() => setIsExpanded(!isExpanded)}>
          <Typography variant="body2" fontWeight="medium">
            Q: {flashcard.question}
          </Typography>
          <Collapsable isExpanded={isExpanded}>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              A: {flashcard.answer}
            </Typography>
          </Collapsable>
        </CardActionArea>
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            display: 'flex',
            gap: 0.5,
          }}
        >
          <Tooltip title="Edit flashcard">
            <IconButton size="small" onClick={handleEditClick} disabled={isDeleting}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete flashcard">
            <IconButton size="small" onClick={handleDeleteClick} disabled={isDeleting}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Card>

      <ConfirmationDialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Flashcard"
        message="Are you sure you want to delete this flashcard?"
        confirmText="Delete"
        confirmColor="error"
        isLoading={isDeleting}
      />
    </li>
  );
};
