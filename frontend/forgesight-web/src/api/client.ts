import axios, { AxiosError, AxiosInstance } from 'axios';

export interface ApiError {
  status: number | null;
  detail: string;
  requestId: string | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

let inMemoryToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null): void {
  inMemoryToken = token;
}

export function registerUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

export const apiClient: AxiosInstance = axios.create({ baseURL: API_BASE_URL });

apiClient.interceptors.request.use((config) => {
  if (inMemoryToken) {
    config.headers.Authorization = `Bearer ${inMemoryToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; request_id?: string }>) => {
    const status = error.response?.status ?? null;
    const detail =
      error.response?.data?.detail ??
      error.message ??
      'An unexpected error occurred. Please try again.';
    const requestId = error.response?.data?.request_id ?? null;

    if (status === 401 && onUnauthorized) {
      onUnauthorized();
    }

    const normalized: ApiError = { status, detail, requestId };
    return Promise.reject(normalized);
  }
);

export function isApiError(error: unknown): error is ApiError {
  return typeof error === 'object' && error !== null && 'detail' in error;
}