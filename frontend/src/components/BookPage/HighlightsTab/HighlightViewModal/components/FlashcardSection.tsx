import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete } from '@/api/generated/flashcards/flashcards.ts';
import { useCreateFlashcardForHighlightApiV1HighlightsHighlightIdFlashcardsPost } from '@/api/generated/highlights/highlights.ts';
import type { Flashcard } from '@/api/generated/model';
import { Collapsable } from '@/components/common/animations/Collapsable.tsx';
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog.tsx';
import { DeleteIcon } from '@/components/common/Icons.tsx';
import { useSnackbar } from '@/contexts/SnackbarContext.tsx';
import {
  Box,
  Button,
  Card,
  CardActionArea,
  IconButton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';

interface FlashcardSectionProps {
  highlightId: number;
  bookId: number;
  flashcards: Flashcard[];
  visible: boolean;
  disabled?: boolean;
}

const Flashcard = ({
  id,
  question,
  answer,
  isLoading,
  onDelete,
}: Flashcard & {
  isLoading: boolean;
  onDelete: (id: number) => void;
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
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
          Q: {question}
        </Typography>
        <Collapsable isExpanded={isExpanded}>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            A: {answer}
          </Typography>
        </Collapsable>
      </CardActionArea>
      <Tooltip title="Delete flashcard">
        <IconButton
          size="small"
          onClick={() => onDelete(id)}
          disabled={isLoading}
          sx={{ position: 'absolute', top: 8, right: 8 }}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Card>
  );
};

export const FlashcardSection = ({
  highlightId,
  bookId,
  flashcards,
  visible,
  disabled = false,
}: FlashcardSectionProps) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);
  const { showSnackbar } = useSnackbar();
  const { isProcessing, saveFlashcard, deleteFlashcard } = useFlashcardMutations(
    bookId,
    highlightId,
    showSnackbar
  );

  const handleDeleteRequest = (flashcardId: number) => {
    setPendingDeleteId(flashcardId);
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (pendingDeleteId === null) return;
    setDeleteConfirmOpen(false);
    await deleteFlashcard(pendingDeleteId);
    setPendingDeleteId(null);
  };

  const isDisabled = disabled || isProcessing;
  const canSave = question.trim() && answer.trim() && !isDisabled;

  const handleSave = async () => {
    await saveFlashcard(question, answer);
    setQuestion('');
    setAnswer('');
  };

  return (
    <AnimatePresence initial={false}>
      {visible && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: 'easeInOut' }}
          style={{ overflow: 'hidden' }}
        >
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Flashcards
            </Typography>

            {/* Existing flashcards */}
            {flashcards.length > 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 2 }}>
                {flashcards.map((flashcard) => (
                  <Flashcard
                    key={flashcard.id}
                    onDelete={() => handleDeleteRequest(flashcard.id)}
                    isLoading={isDisabled}
                    {...flashcard}
                  />
                ))}
              </Box>
            )}

            {/* Create form */}
            <Box
              sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'flex-start' }}
            >
              <TextField
                fullWidth
                size="small"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Question..."
                disabled={isDisabled}
              />
              <TextField
                fullWidth
                size="small"
                multiline
                minRows={2}
                maxRows={4}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Answer..."
                disabled={isDisabled}
              />
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
                <Button
                  variant="text"
                  size="small"
                  onClick={handleSave}
                  disabled={!canSave}
                  sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
                >
                  {isProcessing ? 'Saving...' : 'Add Flashcard'}
                </Button>
              </Box>
            </Box>
          </Box>
        </motion.div>
      )}

      <ConfirmationDialog
        open={deleteConfirmOpen}
        onClose={() => {
          setDeleteConfirmOpen(false);
          setPendingDeleteId(null);
        }}
        onConfirm={handleConfirmDelete}
        title="Delete Flashcard"
        message="Are you sure you want to delete this flashcard?"
        confirmText="Delete"
        confirmColor="error"
        isLoading={isProcessing}
      />
    </AnimatePresence>
  );
};

const useFlashcardMutations = (
  bookId: number,
  highlightId: number,
  showSnackbar: (message: string, severity: 'error' | 'warning' | 'info' | 'success') => void
) => {
  const queryClient = useQueryClient();
  const [isProcessing, setIsProcessing] = useState(false);
  const createFlashcardMutation =
    useCreateFlashcardForHighlightApiV1HighlightsHighlightIdFlashcardsPost({
      mutation: {
        onSuccess: () => {
          void queryClient.invalidateQueries({
            queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
          });
        },
        onError: (error) => {
          console.error('Failed to create flashcard:', error);
          showSnackbar('Failed to create flashcard. Please try again.', 'error');
        },
      },
    });

  const deleteFlashcardMutation = useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete({
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

  const saveFlashcard = async (question: string, answer: string) => {
    if (!question.trim() || !answer.trim()) return;

    setIsProcessing(true);
    try {
      await createFlashcardMutation.mutateAsync({
        highlightId,
        data: { question: question.trim(), answer: answer.trim() },
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const deleteFlashcard = async (flashcardId: number) => {
    await deleteFlashcardMutation.mutateAsync({ flashcardId });
  };

  return {
    isProcessing,
    saveFlashcard,
    deleteFlashcard,
  };
};
