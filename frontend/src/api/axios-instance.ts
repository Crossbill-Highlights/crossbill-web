import Axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { getAccessToken, setAccessToken } from './token-manager';

// Default baseURL - can be overridden by setting AXIOS_INSTANCE.defaults.baseURL
// In development, this points to the local backend server
export const AXIOS_INSTANCE = Axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookie handling for refresh tokens
});

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
// Queue of requests waiting for token refresh
let failedQueue: Array<{
  resolve: (token: string | null) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// Add request interceptor for auth tokens
AXIOS_INSTANCE.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for token refresh on 401
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Only handle 401 errors that haven't been retried
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Don't retry for auth endpoints (login, refresh, logout)
    if (originalRequest.url?.includes('/auth/')) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // If already refreshing, queue this request
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          if (token) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return AXIOS_INSTANCE(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Try to refresh the token
      const response = await AXIOS_INSTANCE.post<{
        access_token: string;
        refresh_token: string;
        expires_in: number;
      }>('/api/v1/auth/refresh', null, {
        withCredentials: true,
      });

      const newToken = response.data.access_token;

      // Update the token manager with the new token
      setAccessToken(newToken, response.data.expires_in);
      processQueue(null, newToken);

      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return AXIOS_INSTANCE(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);

      // Refresh failed, redirect to login
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export const axiosInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  const source = Axios.CancelToken.source();
  const promise = AXIOS_INSTANCE({
    ...config,
    cancelToken: source.token,
  }).then(({ data }) => data);

  // @ts-expect-error - Adding cancel method to promise for Orval
  promise.cancel = () => {
    source.cancel('Query was cancelled');
  };

  return promise;
};
