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
import { CreateFlashcardForm } from '@/pages/BookPage/FlashcardsTab/CreateFlashcardForm.tsx';
import type { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { FlashcardListCard } from '@/pages/BookPage/FlashcardsTab/FlashcardListCard.tsx';
import { FlashcardSuggestions } from '@/pages/BookPage/FlashcardsTab/FlashcardSuggestions.tsx';
import { Box, Stack, Typography } from '@mui/material';
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
