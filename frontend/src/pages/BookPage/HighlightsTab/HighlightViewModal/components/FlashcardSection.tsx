import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete,
  useUpdateFlashcardApiV1FlashcardsFlashcardIdPut,
} from '@/api/generated/flashcards/flashcards.ts';
import {
  useCreateFlashcardForHighlightApiV1HighlightsHighlightIdFlashcardsPost,
  useGetHighlightFlashcardSuggestionsApiV1HighlightsHighlightIdFlashcardSuggestionsGet,
} from '@/api/generated/highlights/highlights.ts';
import type { FlashcardSuggestionItem, Highlight } from '@/api/generated/model';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { FlashcardCard } from '@/pages/BookPage/FlashcardsTab/FlashcardCard.tsx';
import type { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { AISummaryIcon } from '@/theme/Icons.tsx';
import { Box, Button, CircularProgress, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { sortBy } from 'lodash';
import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';

interface FlashcardSectionProps {
  highlight: Highlight;
  bookId: number;
  visible: boolean;
  disabled?: boolean;
}

export const FlashcardSection = ({
  highlight,
  bookId,
  visible,
  disabled = false,
}: FlashcardSectionProps) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [editingFlashcardId, setEditingFlashcardId] = useState<number | null>(null);
  const { showSnackbar } = useSnackbar();
  const { isProcessing, saveFlashcard, updateFlashcard } = useFlashcardMutations(
    bookId,
    highlight.id,
    showSnackbar
  );
  const { isLoading, suggestions, fetchSuggestions } = useAIFlashcardSuggestions(
    highlight.id,
    showSnackbar
  );

  const handleEditFlashcard = (flashcardId: number) => {
    const flashcard = highlight.flashcards.find((f) => f.id === flashcardId);
    if (flashcard) {
      setEditingFlashcardId(flashcardId);
      setQuestion(flashcard.question);
      setAnswer(flashcard.answer);
    }
  };

  const isDisabled = disabled || isProcessing;
  const canSave = question.trim() && answer.trim() && !isDisabled;

  const handleSave = async () => {
    if (editingFlashcardId) {
      await updateFlashcard(editingFlashcardId, question, answer);
    } else {
      await saveFlashcard(question, answer);
    }
    setQuestion('');
    setAnswer('');
    setEditingFlashcardId(null);
  };

  const handleCancelEdit = () => {
    setQuestion('');
    setAnswer('');
    setEditingFlashcardId(null);
  };

  const flashcardsWithContext: FlashcardWithContext[] = sortBy(
    highlight.flashcards.map((flashcard) => ({
      ...flashcard,
      highlight,
      chapterName: highlight.chapter || '',
      chapterId: highlight.chapter_id || 0,
      highlightTags: highlight.highlight_tags,
    })),
    (f) => f.question.toLowerCase()
  );

  const suggestedFlashcardsWithContext: FlashcardWithContext[] = suggestions.map(
    (suggestion, index) => ({
      id: -(index + 1),
      user_id: 0,
      book_id: bookId,
      highlight_id: highlight.id,
      question: suggestion.question,
      answer: suggestion.answer,
      highlight,
      chapterName: highlight.chapter || '',
      chapterId: highlight.chapter_id || 0,
      highlightTags: highlight.highlight_tags,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  );

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
            {flashcardsWithContext.length > 0 && (
              <Box
                component="ul"
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(2, 1fr)',
                  },
                  gap: 2,
                  listStyle: 'none',
                  p: 0,
                  m: 0,
                  mb: 2,
                }}
              >
                {flashcardsWithContext.map((flashcard) => (
                  <li key={flashcard.id}>
                    <FlashcardCard
                      flashcard={flashcard}
                      bookId={bookId}
                      onEdit={() => handleEditFlashcard(flashcard.id)}
                      showSourceHighlight={false}
                    />
                  </li>
                ))}
              </Box>
            )}

            {/* Create form */}
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
                alignItems: 'flex-start',
              }}
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
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, width: '100%' }}>
                {editingFlashcardId && (
                  <Button
                    variant="text"
                    size="small"
                    onClick={handleCancelEdit}
                    disabled={isDisabled}
                    sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
                  >
                    Cancel
                  </Button>
                )}
                <Button
                  variant="text"
                  size="small"
                  onClick={handleSave}
                  disabled={!canSave}
                  sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
                >
                  {isProcessing
                    ? 'Saving...'
                    : editingFlashcardId
                      ? 'Update Flashcard'
                      : 'Add Flashcard'}
                </Button>
              </Box>
            </Box>

            {/* Suggest flashcards button */}
            <AIFeature>
              {suggestions.length ? (
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Suggested flashcards
                </Typography>
              ) : (
                <Button
                  variant="text"
                  size="small"
                  startIcon={<AISummaryIcon />}
                  onClick={fetchSuggestions}
                  disabled={disabled || isLoading}
                  sx={{ mb: 1 }}
                >
                  Suggest flashcards
                </Button>
              )}
              {/* Loading spinner */}
              {isLoading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              )}

              {/* Suggested flashcards */}
              {!isLoading && suggestedFlashcardsWithContext.length > 0 && (
                <Box
                  component="ul"
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: {
                      xs: '1fr',
                      sm: 'repeat(2, 1fr)',
                    },
                    gap: 2,
                    listStyle: 'none',
                    p: 0,
                    m: 0,
                    mb: 2,
                  }}
                >
                  {suggestedFlashcardsWithContext.map((flashcard) => (
                    <li key={flashcard.id}>
                      <FlashcardCard
                        flashcard={flashcard}
                        bookId={bookId}
                        onEdit={() => {}}
                        showSourceHighlight={false}
                        variant="suggestion"
                      />
                    </li>
                  ))}
                </Box>
              )}
            </AIFeature>
          </Box>
        </motion.div>
      )}
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

  const updateFlashcardMutation = useUpdateFlashcardApiV1FlashcardsFlashcardIdPut({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to update flashcard:', error);
        showSnackbar('Failed to update flashcard. Please try again.', 'error');
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

  const updateFlashcard = async (flashcardId: number, question: string, answer: string) => {
    if (!question.trim() || !answer.trim()) return;

    setIsProcessing(true);
    try {
      await updateFlashcardMutation.mutateAsync({
        flashcardId,
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
    updateFlashcard,
    deleteFlashcard,
  };
};

const useAIFlashcardSuggestions = (
  highlightId: number,
  showSnackbar: (message: string, severity: 'error' | 'warning' | 'info' | 'success') => void
) => {
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<FlashcardSuggestionItem[]>([]);

  const { refetch } =
    useGetHighlightFlashcardSuggestionsApiV1HighlightsHighlightIdFlashcardSuggestionsGet(
      highlightId,
      {
        query: {
          enabled: false,
        },
      }
    );

  const fetchSuggestions = async () => {
    setIsLoading(true);
    try {
      const { data } = await refetch();
      if (data?.suggestions) {
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Failed to fetch flashcard suggestions:', error);
      showSnackbar('Failed to fetch suggestions. Please try again.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, suggestions, fetchSuggestions };
};
