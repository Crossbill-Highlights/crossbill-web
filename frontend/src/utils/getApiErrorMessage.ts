interface ApiErrorShape {
  response?: {
    data?: {
      /** Preferred field emitted by the backend's global domain-error handler. */
      message?: string;
      /** Legacy/framework field (e.g. FastAPI's default error body). */
      detail?: string;
    };
  };
}

/**
 * Extract a human-readable message from an API error response.
 *
 * The backend is being unified toward `{ error, message }`, but some responses
 * still use `{ detail }`. Prefer `message`, then `detail`, then the fallback.
 */
export const getApiErrorMessage = (error: unknown, fallback: string): string => {
  const data = (error as ApiErrorShape | null)?.response?.data;
  return data?.message || data?.detail || fallback;
};
