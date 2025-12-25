import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books';
import { useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete } from '@/api/generated/flashcards/flashcards';
import { useCreateFlashcardForHighlightApiV1HighlightsHighlightIdFlashcardsPost } from '@/api/generated/highlights/highlights';
import type { Flashcard } from '@/api/generated/model';
import { Collapsable } from '@/components/common/animations/Collapsable';
import { Delete as DeleteIcon } from '@mui/icons-material';
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
  const queryClient = useQueryClient();
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isSaving, setIsSaving] = useState(false);

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
          alert('Failed to create flashcard. Please try again.');
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
        alert('Failed to delete flashcard. Please try again.');
      },
    },
  });

  const handleSave = async () => {
    if (!question.trim() || !answer.trim()) return;

    setIsSaving(true);
    try {
      await createFlashcardMutation.mutateAsync({
        highlightId,
        data: { question: question.trim(), answer: answer.trim() },
      });
      setQuestion('');
      setAnswer('');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (flashcardId: number) => {
    if (!confirm('Are you sure you want to delete this flashcard?')) return;

    await deleteFlashcardMutation.mutateAsync({ flashcardId });
  };

  const isLoading = disabled || isSaving;
  const canSave = question.trim() && answer.trim() && !isLoading;

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
                    onDelete={handleDelete}
                    isLoading={isLoading}
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
                disabled={isLoading}
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
                disabled={isLoading}
              />
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
                <Button
                  variant="text"
                  size="small"
                  onClick={handleSave}
                  disabled={!canSave}
                  sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
                >
                  {isSaving ? 'Saving...' : 'Add Flashcard'}
                </Button>
              </Box>
            </Box>
          </Box>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
