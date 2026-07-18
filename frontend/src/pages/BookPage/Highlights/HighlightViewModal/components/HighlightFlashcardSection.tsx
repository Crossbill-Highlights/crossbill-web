import { useGetHighlightFlashcardSuggestionsApiV1HighlightsHighlightIdFlashcardSuggestionsGet } from '@/api/generated/flashcards/flashcards.ts';
import { useCreateFlashcardForHighlightApiV1HighlightsHighlightIdFlashcardsPost } from '@/api/generated/highlights/highlights.ts';
import type { Highlight } from '@/api/generated/model';
import type { FlashcardWithContext } from '@/pages/BookPage/Flashcards/FlashcardChapterList.tsx';
import { FlashcardSection } from '@/pages/BookPage/Flashcards/FlashcardSection.tsx';
import { useAIFlashcardSuggestions } from '@/pages/BookPage/Flashcards/hooks/useAIFlashcardSuggestions.ts';
import { useFlashcardMutations } from '@/pages/BookPage/Flashcards/hooks/useFlashcardMutations.ts';
import { sortBy } from 'lodash';

interface HighlightFlashcardSectionProps {
  highlight: Highlight;
  bookId: number;
  visible: boolean;
  disabled?: boolean;
}

/** Wires the shared FlashcardSection to a highlight's cards and endpoints. */
export const HighlightFlashcardSection = ({
  highlight,
  bookId,
  visible,
  disabled = false,
}: HighlightFlashcardSectionProps) => {
  const createFlashcardMutation =
    useCreateFlashcardForHighlightApiV1HighlightsHighlightIdFlashcardsPost();
  const { isProcessing, saveFlashcard, updateFlashcard } = useFlashcardMutations({
    bookId,
    createFlashcard: (question, answer) =>
      createFlashcardMutation.mutateAsync({
        highlightId: highlight.id,
        data: { question, answer },
      }),
  });

  const { refetch } =
    useGetHighlightFlashcardSuggestionsApiV1HighlightsHighlightIdFlashcardSuggestionsGet(
      highlight.id,
      {
        query: {
          enabled: false,
        },
      }
    );
  const { isLoading, suggestions, fetchSuggestions, removeSuggestion } = useAIFlashcardSuggestions(
    async () => {
      const result = await refetch();
      if (result.error) throw result.error;
      return result.data;
    }
  );

  const flashcardsWithContext: FlashcardWithContext[] = sortBy(
    highlight.flashcards.map((flashcard) => ({
      ...flashcard,
      highlight,
      chapterName: highlight.chapter || '',
      chapterId: highlight.chapter_id || 0,
      tags: highlight.tags,
    })),
    (f) => f.question.toLowerCase()
  );

  return (
    <FlashcardSection
      flashcards={flashcardsWithContext}
      bookId={bookId}
      visible={visible}
      disabled={disabled}
      isProcessing={isProcessing}
      onSaveFlashcard={saveFlashcard}
      onUpdateFlashcard={updateFlashcard}
      suggestions={suggestions}
      suggestionsLoading={isLoading}
      onFetchSuggestions={fetchSuggestions}
      onRemoveSuggestion={removeSuggestion}
    />
  );
};
