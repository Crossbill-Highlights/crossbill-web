import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useUpdateFlashcardApiV1FlashcardsFlashcardIdPut } from '@/api/generated/flashcards/flashcards.ts';
import { CommonDialog } from '@/components/common/CommonDialog.tsx';
import { FormatQuote as QuoteIcon } from '@mui/icons-material';
import { Box, Button, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import type { FlashcardWithContext } from './FlashcardChapterList';

interface FlashcardEditDialogProps {
  flashcard: FlashcardWithContext;
  bookId: number;
  open: boolean;
  onClose: () => void;
}

export const FlashcardEditDialog = ({
  flashcard,
  bookId,
  open,
  onClose,
}: FlashcardEditDialogProps) => {
  const [question, setQuestion] = useState(flashcard.question);
  const [answer, setAnswer] = useState(flashcard.answer);
  const [isSaving, setIsSaving] = useState(false);
  const queryClient = useQueryClient();

  // Reset form when flashcard changes
  useEffect(() => {
    setQuestion(flashcard.question);
    setAnswer(flashcard.answer);
  }, [flashcard]);

  const updateMutation = useUpdateFlashcardApiV1FlashcardsFlashcardIdPut({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
        onClose();
      },
      onError: (error) => {
        console.error('Failed to update flashcard:', error);
        alert('Failed to update flashcard. Please try again.');
      },
    },
  });

  const handleSave = async () => {
    if (!question.trim() || !answer.trim()) return;

    setIsSaving(true);
    try {
      await updateMutation.mutateAsync({
        flashcardId: flashcard.id,
        data: {
          question: question.trim(),
          answer: answer.trim(),
        },
      });
    } finally {
      setIsSaving(false);
    }
  };

  const hasChanges = question.trim() !== flashcard.question || answer.trim() !== flashcard.answer;
  const canSave = hasChanges && question.trim() && answer.trim() && !isSaving;

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      title="Edit Flashcard"
      maxWidth="sm"
      isLoading={isSaving}
      footerActions={
        <Box sx={{ display: 'flex', gap: 1, width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave} disabled={!canSave}>
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Box>
      }
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Source highlight context */}
        {flashcard.highlightText && (
          <Box
            sx={{
              p: 2,
              bgcolor: 'action.hover',
              borderRadius: 2,
              borderLeft: '3px solid',
              borderLeftColor: 'primary.light',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
              <QuoteIcon sx={{ fontSize: 18, color: 'text.disabled', mt: 0.25, flexShrink: 0 }} />
              <Box>
                <Typography
                  variant="caption"
                  sx={{
                    color: 'text.secondary',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    display: 'block',
                    mb: 0.5,
                  }}
                >
                  Source Highlight
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ color: 'text.secondary', fontStyle: 'italic', lineHeight: 1.5 }}
                >
                  {flashcard.highlightText}
                </Typography>
              </Box>
            </Box>
          </Box>
        )}

        {/* Question field */}
        <Box>
          <Typography
            variant="caption"
            sx={{
              color: 'primary.main',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              display: 'block',
              mb: 1,
            }}
          >
            Question
          </Typography>
          <TextField
            fullWidth
            multiline
            minRows={2}
            maxRows={4}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question..."
            disabled={isSaving}
            error={!question.trim()}
            helperText={!question.trim() ? 'Question is required' : ''}
          />
        </Box>

        {/* Answer field */}
        <Box>
          <Typography
            variant="caption"
            sx={{
              color: 'secondary.main',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              display: 'block',
              mb: 1,
            }}
          >
            Answer
          </Typography>
          <TextField
            fullWidth
            multiline
            minRows={3}
            maxRows={6}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Enter your answer..."
            disabled={isSaving}
            error={!answer.trim()}
            helperText={!answer.trim() ? 'Answer is required' : ''}
          />
        </Box>
      </Box>
    </CommonDialog>
  );
};
