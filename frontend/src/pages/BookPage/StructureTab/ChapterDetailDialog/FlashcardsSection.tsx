import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  useCreateFlashcardForBookApiV1BooksBookIdFlashcardsPost,
  useGetChapterFlashcardSuggestionsApiV1ChaptersChapterIdFlashcardSuggestionsGet,
  useUpdateFlashcardApiV1FlashcardsFlashcardIdPut,
} from '@/api/generated/flashcards/flashcards.ts';
import type {
  ChapterPrereadingResponse,
  ChapterWithHighlights,
  FlashcardSuggestionItem,
} from '@/api/generated/model';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import type { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { FlashcardEditDialog } from '@/pages/BookPage/FlashcardsTab/FlashcardEditDialog.tsx';
import { FlashcardListCard } from '@/pages/BookPage/FlashcardsTab/FlashcardListCard.tsx';
import { FlashcardSuggestionCard } from '@/pages/BookPage/FlashcardsTab/FlashcardSuggestionCard.tsx';
import { AIIcon } from '@/theme/Icons.tsx';
import { Box, Button, CircularProgress, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { flatMap } from 'lodash';
import { useCallback, useMemo, useState } from 'react';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface FlashcardsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
  prereadingSummary?: ChapterPrereadingResponse;
}

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
          startIcon={<AIIcon />}
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

const useFlashcardMutations = (
  bookId: number,
  chapterId: number,
  showSnackbar: (message: string, severity: 'error' | 'warning' | 'info' | 'success') => void
) => {
  const queryClient = useQueryClient();
  const [isProcessing, setIsProcessing] = useState(false);

  const createFlashcardMutation = useCreateFlashcardForBookApiV1BooksBookIdFlashcardsPost({
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

  const saveFlashcard = async (question: string, answer: string) => {
    if (!question.trim() || !answer.trim()) return;

    setIsProcessing(true);
    try {
      await createFlashcardMutation.mutateAsync({
        bookId,
        data: { question: question.trim(), answer: answer.trim(), chapter_id: chapterId },
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

  return {
    isProcessing,
    saveFlashcard,
    updateFlashcard,
  };
};

const useAIFlashcardSuggestions = (
  chapterId: number,
  showSnackbar: (message: string, severity: 'error' | 'warning' | 'info' | 'success') => void
) => {
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<FlashcardSuggestionItem[]>([]);

  const { refetch } =
    useGetChapterFlashcardSuggestionsApiV1ChaptersChapterIdFlashcardSuggestionsGet(chapterId, {
      query: {
        enabled: false,
      },
    });

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

export const FlashcardsSection = ({
  chapter,
  bookId,
  prereadingSummary,
}: FlashcardsSectionProps) => {
  const [editingFlashcard, setEditingFlashcard] = useState<FlashcardWithContext | null>(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [editingFlashcardId, setEditingFlashcardId] = useState<number | null>(null);
  const { showSnackbar } = useSnackbar();
  const { isProcessing, saveFlashcard, updateFlashcard } = useFlashcardMutations(
    bookId,
    chapter.id,
    showSnackbar
  );
  const { isLoading, suggestions, fetchSuggestions, removeSuggestion } = useAIFlashcardSuggestions(
    chapter.id,
    showSnackbar
  );

  const flashcardsWithContext = useMemo(
    (): FlashcardWithContext[] =>
      flatMap(chapter.highlights, (highlight) =>
        highlight.flashcards.map((flashcard) => ({
          ...flashcard,
          highlight,
          chapterName: chapter.name,
          chapterId: chapter.id,
          highlightTags: highlight.highlight_tags,
        }))
      ),
    [chapter]
  );

  const count = flashcardsWithContext.length;

  const handleEditFlashcard = useCallback((flashcard: FlashcardWithContext) => {
    setEditingFlashcard(flashcard);
  }, []);

  const handleCloseEdit = useCallback(() => {
    setEditingFlashcard(null);
  }, []);

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

  return (
    <>
      <CollapsibleSection title="Flashcards" count={count} defaultExpanded={count > 0}>
        {flashcardsWithContext.length > 0 && (
          <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0, mb: 2 }}>
            {flashcardsWithContext.map((flashcard) => (
              <li key={flashcard.id}>
                <FlashcardListCard
                  flashcard={flashcard}
                  bookId={bookId}
                  onEdit={() => handleEditFlashcard(flashcard)}
                  showSourceHighlight={false}
                />
              </li>
            ))}
          </Stack>
        )}

        <CreateFlashcardForm
          question={question}
          answer={answer}
          onQuestionChange={setQuestion}
          onAnswerChange={setAnswer}
          editingFlashcardId={editingFlashcardId}
          isDisabled={isProcessing}
          isProcessing={isProcessing}
          onSave={handleSave}
          onCancelEdit={handleCancelEdit}
        />

        {prereadingSummary && (
          <AIFeature>
            <FlashcardSuggestions
              suggestions={suggestions}
              isLoading={isLoading}
              disabled={false}
              onFetchSuggestions={fetchSuggestions}
              onAcceptSuggestion={handleAcceptSuggestion}
              onRejectSuggestion={removeSuggestion}
            />
          </AIFeature>
        )}
      </CollapsibleSection>

      {editingFlashcard && (
        <FlashcardEditDialog
          flashcard={editingFlashcard}
          bookId={bookId}
          open={true}
          onClose={handleCloseEdit}
        />
      )}
    </>
  );
};
