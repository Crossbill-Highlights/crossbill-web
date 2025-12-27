import { useEffect, useState } from 'react';

import { axiosInstance } from '../api/axios-instance';

interface UseAuthenticatedImageResult {
  objectUrl: string | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Custom hook to fetch an authenticated image and convert it to an object URL.
 *
 * This hook fetches an image using axios (which includes authentication headers)
 * and converts the response to a blob URL that can be used in <img> tags.
 *
 * @param url - The URL to fetch the image from, or null to skip fetching
 * @returns Object containing the blob URL, loading state, and error state
 *
 * @example
 * ```tsx
 * const { objectUrl, loading, error } = useAuthenticatedImage('/api/v1/books/1/cover');
 *
 * if (loading) return <Skeleton />;
 * if (error) return <PlaceholderIcon />;
 * return <img src={objectUrl} alt="Book cover" />;
 * ```
 */
export function useAuthenticatedImage(url: string | null): UseAuthenticatedImageResult {
  const [state, setState] = useState<{
    objectUrl: string | null;
    loading: boolean;
    error: Error | null;
  }>({
    objectUrl: null,
    loading: false,
    error: null,
  });

  useEffect(() => {
    // Skip if no URL provided - state is already initialized to empty
    if (!url) {
      return;
    }

    let isMounted = true;
    let currentObjectUrl: string | null = null;

    const fetchImage = async () => {
      // Set loading at the start of fetch
      if (isMounted) {
        setState((prev) => ({ ...prev, loading: true, error: null }));
      }

      try {
        // Fetch image with auth headers via axios instance
        // Note: axiosInstance returns data directly, not the full response
        const blob = await axiosInstance<Blob>({
          url,
          method: 'GET',
          responseType: 'blob',
        });

        if (isMounted) {
          // Create object URL from blob
          currentObjectUrl = URL.createObjectURL(blob);
          setState({ objectUrl: currentObjectUrl, loading: false, error: null });
        } else {
          // Component unmounted before response - clean up immediately
          URL.revokeObjectURL(URL.createObjectURL(blob));
        }
      } catch (err) {
        if (isMounted) {
          setState({
            objectUrl: null,
            loading: false,
            error: err instanceof Error ? err : new Error('Failed to load image'),
          });
        }
      }
    };

    fetchImage();

    // Cleanup function
    return () => {
      isMounted = false;
      // Revoke object URL to prevent memory leaks
      if (currentObjectUrl) {
        URL.revokeObjectURL(currentObjectUrl);
      }
    };
  }, [url]);

  return state;
}
