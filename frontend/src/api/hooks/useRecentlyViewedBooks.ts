/**
 * Custom hook for fetching recently viewed books.
 * This will be replaced by the generated hook when running `npm run api:generate`.
 */
import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';

import type { BookWithHighlightCount, HTTPValidationError } from '../generated/model';

import { axiosInstance } from '../axios-instance';

export interface RecentlyViewedBooksResponse {
  books: BookWithHighlightCount[];
}

export interface GetRecentlyViewedBooksParams {
  limit?: number;
}

export const getRecentlyViewedBooksApiV1BooksRecentlyViewedGet = (
  params?: GetRecentlyViewedBooksParams,
  signal?: AbortSignal
) => {
  return axiosInstance<RecentlyViewedBooksResponse>({
    url: `/api/v1/books/recently-viewed`,
    method: 'GET',
    params,
    signal,
  });
};

export const getGetRecentlyViewedBooksQueryKey = (params?: GetRecentlyViewedBooksParams) => {
  return [`/api/v1/books/recently-viewed`, ...(params ? [params] : [])] as const;
};

export function useGetRecentlyViewedBooks<
  TData = Awaited<ReturnType<typeof getRecentlyViewedBooksApiV1BooksRecentlyViewedGet>>,
  TError = HTTPValidationError,
>(
  params?: GetRecentlyViewedBooksParams,
  options?: {
    query?: Partial<
      UseQueryOptions<
        Awaited<ReturnType<typeof getRecentlyViewedBooksApiV1BooksRecentlyViewedGet>>,
        TError,
        TData
      >
    >;
  }
): UseQueryResult<TData, TError> {
  const { query: queryOptions } = options ?? {};

  const queryKey = queryOptions?.queryKey ?? getGetRecentlyViewedBooksQueryKey(params);

  const queryFn = ({ signal }: { signal?: AbortSignal }) =>
    getRecentlyViewedBooksApiV1BooksRecentlyViewedGet(params, signal);

  return useQuery({
    queryKey,
    queryFn,
    ...queryOptions,
  });
}
