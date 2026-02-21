import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import {
  useCreateFlashcardForBookApiV1BooksBookIdFlashcardsPost,
  useGetChapterFlashcardSuggestionsApiV1ChaptersChapterIdFlashcardSuggestionsGet,
  useUpdateFlashcardApiV1FlashcardsFlashcardIdPut,
} from '@/api/generated/flashcards/flashcards.ts';
import type {
  ChapterPrereadingResponse,
  ChapterWithHighlights,
  Flashcard,
  FlashcardSuggestionItem,
} from '@/api/generated/model';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { CreateFlashcardForm } from '@/pages/BookPage/FlashcardsTab/CreateFlashcardForm.tsx';
import type { FlashcardWithContext } from '@/pages/BookPage/FlashcardsTab/FlashcardChapterList.tsx';
import { FlashcardEditDialog } from '@/pages/BookPage/FlashcardsTab/FlashcardEditDialog.tsx';
import { FlashcardListCard } from '@/pages/BookPage/FlashcardsTab/FlashcardListCard.tsx';
import { FlashcardSuggestions } from '@/pages/BookPage/FlashcardsTab/FlashcardSuggestions.tsx';
import { Stack } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { flatMap } from 'lodash';
import { useCallback, useMemo, useState } from 'react';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface FlashcardsSectionProps {
  chapter: ChapterWithHighlights;
  bookId: number;
  prereadingSummary?: ChapterPrereadingResponse;
  bookFlashcards?: Flashcard[];
}

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
  bookFlashcards,
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

  const flashcardsWithContext = useMemo((): FlashcardWithContext[] => {
    const highlightFlashcards = flatMap(chapter.highlights, (highlight) =>
      highlight.flashcards.map((flashcard) => ({
        ...flashcard,
        highlight,
        chapterName: chapter.name,
        chapterId: chapter.id,
        highlightTags: highlight.highlight_tags,
      }))
    );

    const chapterLinkedFlashcards: FlashcardWithContext[] = (bookFlashcards ?? [])
      .filter((fc) => fc.chapter_id === chapter.id)
      .map((fc) => ({
        ...fc,
        highlight: null,
        chapterName: chapter.name,
        chapterId: chapter.id,
        highlightTags: [],
      }));

    return [...highlightFlashcards, ...chapterLinkedFlashcards];
  }, [chapter, bookFlashcards]);

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
