import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete } from '@/api/generated/flashcards/flashcards.ts';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { FlashcardContent } from '@/pages/BookPage/FlashcardsTab/FlashcardContent.tsx';
import { DeleteIcon, EditIcon } from '@/theme/Icons.tsx';
import { Box, Card, CardActionArea, CardContent, styled } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

export interface FlashcardCardProps {
  flashcard: FlashcardWithContext;
  bookId: number;
  onEdit: () => void;
  component?: React.ElementType;
  showSourceHighlight?: boolean;
}

const FlashcardStyled = styled(Card)(({ theme }) => ({
  height: 'fit-content',
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  transition: 'all 0.2s ease',
  bgcolor: 'background.paper',
  border: `1px solid ${theme.palette.divider}`,
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: 3,
  },
}));

const ActionButtonsStyled = styled(Box)(() => ({
  position: 'absolute',
  top: 8,
  right: 8,
  display: 'flex',
  gap: 0.5,
  zIndex: 1,
  opacity: 0.7,
  transition: 'opacity 0.2s ease',
  '&:hover': {
    opacity: 1,
  },
}));

export const FlashcardCard = ({
  flashcard,
  bookId,
  onEdit,
  showSourceHighlight = true,
}: FlashcardCardProps) => {
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
    <FlashcardStyled>
      <CardActionArea
        onClick={() => setIsExpanded(!isExpanded)}
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'stretch',
          justifyContent: 'flex-start',
        }}
      >
        <CardContent sx={{ width: '100%', pt: 2 }}>
          <FlashcardContent
            question={flashcard.question}
            answer={flashcard.answer}
            isExpanded={isExpanded}
            showSourceHighlight={showSourceHighlight}
            sourceHighlightText={flashcard.highlight.text}
          />
        </CardContent>
      </CardActionArea>
      <ActionButtonsStyled>
        <IconButtonWithTooltip
          title="Edit"
          ariaLabel="Edit flashcard"
          onClick={onEdit}
          disabled={isDeleting}
          icon={<EditIcon fontSize="small" />}
        />
        <IconButtonWithTooltip
          title="Delete"
          ariaLabel="Delete flashcard"
          onClick={handleDeleteClick}
          disabled={isDeleting}
          icon={<DeleteIcon fontSize="small" />}
        />
      </ActionButtonsStyled>

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
    </FlashcardStyled>
  );
};
