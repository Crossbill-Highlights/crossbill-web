/**
 * Temporary API client for book update endpoint
 * This should be replaced by Orval-generated hooks once the backend is running
 * and you run: npm run api:generate
 */

import { useMutation, UseMutationOptions, useQueryClient } from '@tanstack/react-query';
import { axiosInstance } from './axios-instance';

// Type definitions matching the backend schemas
export interface Tag {
  id: number;
  name: string;
}

export interface BookWithHighlightCount {
  id: number;
  title: string;
  author: string | null;
  isbn: string | null;
  cover: string | null;
  highlight_count: number;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

export interface BookUpdateRequest {
  tags: string[];
}

export interface UpdateBookParams {
  bookId: number;
  data: BookUpdateRequest;
}

/**
 * Update a book's information (currently only tags)
 */
export const updateBook = (bookId: number, data: BookUpdateRequest): Promise<BookWithHighlightCount> => {
  return axiosInstance<BookWithHighlightCount>({
    url: `/api/v1/book/${bookId}`,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data,
  });
};

/**
 * Hook for updating a book
 * Follows the Orval-generated hook pattern
 */
export const useUpdateBookApiV1BookBookIdPost = <TError = unknown, TContext = unknown>(options?: {
  mutation?: UseMutationOptions<
    BookWithHighlightCount,
    TError,
    { bookId: number; data: BookUpdateRequest },
    TContext
  >;
}) => {
  const { mutation: mutationOptions } = options ?? {};
  const queryClient = useQueryClient();

  return useMutation<BookWithHighlightCount, TError, { bookId: number; data: BookUpdateRequest }, TContext>({
    mutationFn: ({ bookId, data }) => updateBook(bookId, data),
    onSuccess: async (data, variables, context) => {
      // Invalidate all queries to ensure fresh data everywhere
      // This is safer than trying to match specific Orval-generated query keys
      await queryClient.invalidateQueries();

      // Call user-provided onSuccess if exists
      // This will be called after the invalidation completes
      await mutationOptions?.onSuccess?.(data, variables, context);
    },
    ...mutationOptions,
  });
};
