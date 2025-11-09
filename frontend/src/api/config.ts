import { AXIOS_INSTANCE } from './axios-instance';

/**
 * Configure the API client with environment-specific settings.
 * This should be called once at application startup.
 */
export const configureApiClient = () => {
  // Override baseURL with environment variable if provided
  const apiUrl = import.meta.env.VITE_API_URL;
  if (apiUrl) {
    AXIOS_INSTANCE.defaults.baseURL = apiUrl as string;
  }
};
