import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey,
  useAddTagToHighlightApiV1BooksBookIdHighlightHighlightIdTagPost,
  useRemoveTagFromHighlightApiV1BooksBookIdHighlightHighlightIdTagTagIdDelete,
} from '@/api/generated/books/books.ts';
import type { HighlightTagInBook } from '@/api/generated/model';
import { useQueryClient } from '@tanstack/react-query';
import { filter, map } from 'lodash';
import { useEffect, useState } from 'react';

export interface UseImmediateTagMutationParams {
  /** Book ID for API calls */
  bookId: number;
  /** Highlight ID for API calls */
  highlightId: number;
  /** Initial tags for the highlight */
  initialTags: HighlightTagInBook[];
  /** Snackbar function for error/success notifications */
  showSnackbar: (message: string, severity: 'error' | 'success' | 'info' | 'warning') => void;
}

export interface UseImmediateTagMutationReturn {
  /** Whether a mutation is currently processing */
  isProcessing: boolean;
  /** Current list of tags */
  currentTags: HighlightTagInBook[];
  /** Function to update the tag list - handles add/remove mutations */
  updateTagList: (newValue: (HighlightTagInBook | string)[]) => Promise<void>;
}

const calculateAddedTags = (current: string[], updated: string[]): string[] => {
  return filter(updated, (name) => !current.includes(name));
};

const calculateRemovedTags = (
  current: HighlightTagInBook[],
  updated: string[]
): HighlightTagInBook[] => {
  return filter(current, (tag) => !updated.includes(tag.name));
};

/**
 * Hook for managing immediate tag mutations on highlights
 * Handles adding and removing tags with optimistic updates and error handling
 *
 * @param params - Configuration for the hook
 * @returns Object with processing state, current tags, and update function
 *
 * @example
 * ```tsx
 * const { isProcessing, currentTags, updateTagList } = useImmediateTagMutation({
 *   bookId: 1,
 *   highlightId: 123,
 *   initialTags: highlight.highlight_tags,
 *   showSnackbar,
 * });
 * ```
 */
export const useImmediateTagMutation = ({
  bookId,
  highlightId,
  initialTags,
  showSnackbar,
}: UseImmediateTagMutationParams): UseImmediateTagMutationReturn => {
  const queryClient = useQueryClient();
  const [currentTags, setCurrentTags] = useState<HighlightTagInBook[]>(initialTags);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    setCurrentTags(initialTags);
  }, [highlightId, initialTags]);

  const addTagMutation = useAddTagToHighlightApiV1BooksBookIdHighlightHighlightIdTagPost({
    mutation: {
      onSuccess: (data) => {
        setCurrentTags(data.highlight_tags);
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
        void queryClient.invalidateQueries({
          queryKey: getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to add tag:', error);
        showSnackbar('Failed to add tag. Please try again.', 'error');
      },
    },
  });

  const removeTagMutation =
    useRemoveTagFromHighlightApiV1BooksBookIdHighlightHighlightIdTagTagIdDelete({
      mutation: {
        onSuccess: (data) => {
          setCurrentTags(data.highlight_tags);
          void queryClient.invalidateQueries({
            queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
          });
          void queryClient.invalidateQueries({
            queryKey: getGetHighlightTagsApiV1BooksBookIdHighlightTagsGetQueryKey(bookId),
          });
        },
        onError: (error) => {
          console.error('Failed to remove tag:', error);
          showSnackbar('Failed to remove tag. Please try again.', 'error');
        },
      },
    });

  const addTagToHighlight = async (tagName: string) => {
    setIsProcessing(true);
    try {
      await addTagMutation.mutateAsync({
        bookId,
        highlightId,
        data: { name: tagName },
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const removeTagFromHighlight = async (tagId: number) => {
    setIsProcessing(true);
    try {
      await removeTagMutation.mutateAsync({
        bookId,
        highlightId,
        tagId,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const updateTagList = async (newValue: (HighlightTagInBook | string)[]) => {
    const currentTagNames = map(currentTags, (t) => t.name);
    const newTagNames = map(newValue, (v) => (typeof v === 'string' ? v : v.name));

    const addedTags = calculateAddedTags(currentTagNames, newTagNames);
    const removedTags = calculateRemovedTags(currentTags, newTagNames);

    for (const tagName of addedTags) {
      await addTagToHighlight(tagName);
    }

    for (const tag of removedTags) {
      await removeTagFromHighlight(tag.id);
    }
  };

  return {
    isProcessing,
    currentTags,
    updateTagList,
  };
};
