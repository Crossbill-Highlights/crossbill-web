import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books.ts';
import { useUpdateFlashcardApiV1FlashcardsFlashcardIdPut } from '@/api/generated/flashcards/flashcards.ts';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useQueryClient, type QueryKey } from '@tanstack/react-query';
import { useState } from 'react';

interface UseFlashcardMutationsOptions {
  bookId: number;
  /** Source-specific create call (e.g. POST to a highlight's or note's flashcards). */
  createFlashcard: (question: string, answer: string) => Promise<unknown>;
  /** Query keys to invalidate in addition to the book details query. */
  additionalInvalidateKeys?: QueryKey[];
}

/**
 * Save/update mutations for flashcards shown in an entity view modal.
 * Update goes through the source-agnostic PUT /flashcards/:id endpoint;
 * create is delegated to the caller since it is source-specific.
 */
export const useFlashcardMutations = ({
  bookId,
  createFlashcard,
  additionalInvalidateKeys = [],
}: UseFlashcardMutationsOptions) => {
  const queryClient = useQueryClient();
  const { showSnackbar } = useSnackbar();
  const [isProcessing, setIsProcessing] = useState(false);

  const invalidateFlashcardQueries = () => {
    void queryClient.invalidateQueries({
      queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
    });
    for (const queryKey of additionalInvalidateKeys) {
      void queryClient.invalidateQueries({ queryKey });
    }
  };

  const updateFlashcardMutation = useUpdateFlashcardApiV1FlashcardsFlashcardIdPut({
    mutation: {
      onSuccess: invalidateFlashcardQueries,
      onError: (error) => {
        console.error('Failed to update flashcard:', error);
        showSnackbar('Failed to update flashcard. Please try again.', 'error');
      },
    },
  });

  const saveFlashcard = async (question: string, answer: string): Promise<boolean> => {
    if (!question.trim() || !answer.trim()) return false;

    setIsProcessing(true);
    try {
      await createFlashcard(question.trim(), answer.trim());
      invalidateFlashcardQueries();
      return true;
    } catch (error) {
      console.error('Failed to create flashcard:', error);
      showSnackbar('Failed to create flashcard. Please try again.', 'error');
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  const updateFlashcard = async (
    flashcardId: number,
    question: string,
    answer: string
  ): Promise<boolean> => {
    if (!question.trim() || !answer.trim()) return false;

    setIsProcessing(true);
    try {
      await updateFlashcardMutation.mutateAsync({
        flashcardId,
        data: { question: question.trim(), answer: answer.trim() },
      });
      return true;
    } catch {
      // Already reported via the mutation's onError
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  return { isProcessing, saveFlashcard, updateFlashcard };
};
