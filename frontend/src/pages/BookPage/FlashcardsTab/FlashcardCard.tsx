import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete } from '@/api/generated/flashcards/flashcards.ts';
import { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { Collapsable } from '@/components/animations/Collapsable.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { DeleteIcon, EditIcon, QuoteIcon } from '@/theme/Icons.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  IconButton,
  styled,
  Tooltip,
  Typography,
} from '@mui/material';
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
  borderColor: theme.palette.divider,
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
          {/* Question */}
          <Box
            sx={{
              mb: isExpanded ? 2 : 1,
              pr: 6,
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: 'primary.main',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                display: 'block',
                mb: 0.5,
              }}
            >
              Question
            </Typography>
            <Typography variant="body1" sx={{ lineHeight: 1.5 }}>
              {flashcard.question}
            </Typography>
          </Box>

          <Collapsable isExpanded={isExpanded}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
              <Typography
                variant="caption"
                sx={{
                  color: 'secondary.main',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Answer
              </Typography>
            </Box>

            <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.5 }}>
              {flashcard.answer}
            </Typography>

            {/* Source highlight preview */}
            {showSourceHighlight && flashcard.highlight.text && (
              <Box
                sx={{
                  mt: 2,
                  pt: 2,
                  borderTop: '1px dashed',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
                  <QuoteIcon
                    sx={{ fontSize: 14, color: 'text.disabled', mt: 0.25, flexShrink: 0 }}
                  />
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'text.disabled',
                      fontStyle: 'italic',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      lineHeight: 1.4,
                    }}
                  >
                    {flashcard.highlight.text}
                  </Typography>
                </Box>
              </Box>
            )}
          </Collapsable>
        </CardContent>
      </CardActionArea>
      <ActionButtonsStyled>
        <Tooltip title="Edit">
          <IconButton size="small" onClick={onEdit} disabled={isDeleting}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete">
          <IconButton size="small" onClick={handleDeleteClick} disabled={isDeleting}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
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
