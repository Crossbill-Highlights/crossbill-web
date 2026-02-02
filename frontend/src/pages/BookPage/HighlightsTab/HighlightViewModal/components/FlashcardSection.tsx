import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete,
  useGetHighlightFlashcardSuggestionsApiV1HighlightsHighlightIdFlashcardSuggestionsGet,
  useUpdateFlashcardApiV1FlashcardsFlashcardIdPut,
} from '@/api/generated/flashcards/flashcards.ts';
import { useCreateFlashcardForHighlightApiV1HighlightsHighlightIdFlashcardsPost } from '@/api/generated/highlights/highlights.ts';
import type { FlashcardSuggestionItem, Highlight } from '@/api/generated/model';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import type { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { FlashcardListCard } from '@/pages/BookPage/FlashcardsTab/FlashcardListCard.tsx';
import { FlashcardSuggestionCard } from '@/pages/BookPage/FlashcardsTab/FlashcardSuggestionCard.tsx';
import { AISummaryIcon } from '@/theme/Icons.tsx';
import { Box, Button, CircularProgress, Stack, TextField, Typography } from '@mui/material';
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

interface FlashcardsListProps {
  flashcardsWithContext: FlashcardWithContext[];
  bookId: number;
  onEdit: (flashcardId: number) => void;
}

const FlashcardsList = ({ flashcardsWithContext, bookId, onEdit }: FlashcardsListProps) => {
  if (flashcardsWithContext.length === 0) {
    return null;
  }

  return (
    <Stack
      component="ul"
      sx={{
        gap: 2,
        listStyle: 'none',
        p: 0,
        m: 0,
        mb: 2,
      }}
    >
      {flashcardsWithContext.map((flashcard) => (
        <li key={flashcard.id}>
          <FlashcardListCard
            flashcard={flashcard}
            bookId={bookId}
            onEdit={() => onEdit(flashcard.id)}
            showSourceHighlight={false}
          />
        </li>
      ))}
    </Stack>
  );
};

interface CreateFlashcardFormProps {
  question: string;
  answer: string;
  onQuestionChange: (value: string) => void;
  onAnswerChange: (value: string) => void;
  editingFlashcardId: number | null;
  isDisabled: boolean;
  isProcessing: boolean;
  onSave: () => void;
  onCancelEdit: () => void;
}

const CreateFlashcardForm = ({
  question,
  answer,
  onQuestionChange,
  onAnswerChange,
  editingFlashcardId,
  isDisabled,
  isProcessing,
  onSave,
  onCancelEdit,
}: CreateFlashcardFormProps) => {
  const canSave = question.trim() && answer.trim() && !isDisabled;

  return (
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
        onChange={(e) => onQuestionChange(e.target.value)}
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
        onChange={(e) => onAnswerChange(e.target.value)}
        placeholder="Answer..."
        disabled={isDisabled}
      />
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, width: '100%' }}>
        {editingFlashcardId && (
          <Button
            variant="text"
            size="small"
            onClick={onCancelEdit}
            disabled={isDisabled}
            sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
          >
            Cancel
          </Button>
        )}
        <Button
          variant="text"
          size="small"
          onClick={onSave}
          disabled={!canSave}
          sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
        >
          {isProcessing ? 'Saving...' : editingFlashcardId ? 'Update Flashcard' : 'Add Flashcard'}
        </Button>
      </Box>
    </Box>
  );
};

interface FlashcardSuggestionsProps {
  suggestions: FlashcardSuggestionItem[];
  isLoading: boolean;
  disabled: boolean;
  onFetchSuggestions: () => void;
  onAcceptSuggestion: (suggestion: FlashcardSuggestionItem, index: number) => void;
  onRejectSuggestion: (index: number) => void;
}

const FlashcardSuggestions = ({
  suggestions,
  isLoading,
  disabled,
  onFetchSuggestions,
  onAcceptSuggestion,
  onRejectSuggestion,
}: FlashcardSuggestionsProps) => {
  return (
    <>
      {suggestions.length ? (
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Suggested flashcards
        </Typography>
      ) : (
        <Button
          variant="text"
          size="small"
          startIcon={<AISummaryIcon />}
          onClick={onFetchSuggestions}
          disabled={disabled || isLoading}
          sx={{ mb: 1 }}
        >
          Suggest flashcards
        </Button>
      )}

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {!isLoading && suggestions.length > 0 && (
        <Stack
          component="ul"
          sx={{
            gap: 2,
            listStyle: 'none',
            p: 0,
            m: 0,
            mb: 2,
          }}
        >
          {suggestions.map((suggestion, index) => (
            <li key={index}>
              <FlashcardSuggestionCard
                question={suggestion.question}
                answer={suggestion.answer}
                onAccept={() => onAcceptSuggestion(suggestion, index)}
                onReject={() => onRejectSuggestion(index)}
              />
            </li>
          ))}
        </Stack>
      )}
    </>
  );
};

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
  const { isLoading, suggestions, fetchSuggestions, removeSuggestion } = useAIFlashcardSuggestions(
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

  const handleAcceptSuggestion = async (suggestion: FlashcardSuggestionItem, index: number) => {
    await saveFlashcard(suggestion.question, suggestion.answer);
    removeSuggestion(index);
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

            <FlashcardsList
              flashcardsWithContext={flashcardsWithContext}
              bookId={bookId}
              onEdit={handleEditFlashcard}
            />

            <CreateFlashcardForm
              question={question}
              answer={answer}
              onQuestionChange={setQuestion}
              onAnswerChange={setAnswer}
              editingFlashcardId={editingFlashcardId}
              isDisabled={disabled || isProcessing}
              isProcessing={isProcessing}
              onSave={handleSave}
              onCancelEdit={handleCancelEdit}
            />

            <AIFeature>
              <FlashcardSuggestions
                suggestions={suggestions}
                isLoading={isLoading}
                disabled={disabled}
                onFetchSuggestions={fetchSuggestions}
                onAcceptSuggestion={handleAcceptSuggestion}
                onRejectSuggestion={removeSuggestion}
              />
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

  const removeSuggestion = (index: number) => {
    setSuggestions((prev) => prev.filter((_, i) => i !== index));
  };

  return { isLoading, suggestions, fetchSuggestions, removeSuggestion };
};
