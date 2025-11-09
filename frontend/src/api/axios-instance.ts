import Axios, { AxiosRequestConfig } from 'axios';

// Default baseURL - can be overridden by setting AXIOS_INSTANCE.defaults.baseURL
// In development, this points to the local backend server
export const AXIOS_INSTANCE = Axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth tokens (future)
AXIOS_INSTANCE.interceptors.request.use(
  (config) => {
    // Future: Add auth token here
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Future: Handle unauthorized
    }
    return Promise.reject(error);
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
