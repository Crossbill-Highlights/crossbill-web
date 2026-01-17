import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete } from '@/api/generated/flashcards/flashcards.ts';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { FlashcardCard } from '@/pages/BookPage/FlashcardsTab/FlashcardCard.tsx';
import { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { DeleteIcon, EditIcon } from '@/theme/Icons.tsx';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

export interface FlashcardListCardProps {
  flashcard: FlashcardWithContext;
  bookId: number;
  onEdit: () => void;
  showSourceHighlight?: boolean;
}

export const FlashcardListCard = ({
  flashcard,
  bookId,
  onEdit,
  showSourceHighlight = true,
}: FlashcardListCardProps) => {
  const [isDeleting, setIsDeleting] = useState(false);
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
    <>
      <FlashcardCard
        question={flashcard.question}
        answer={flashcard.answer}
        showSourceHighlight={showSourceHighlight}
        sourceHighlightText={flashcard.highlight.text}
        renderActions={() => (
          <>
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
          </>
        )}
      />

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
    </>
  );
};
