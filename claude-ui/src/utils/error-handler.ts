import { AxiosError } from 'axios';

interface ErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

/**
 * Extract meaningful error message from various error types
 */
export const getErrorMessage = (error: unknown): string => {
  // Handle Axios errors
  if (error instanceof AxiosError) {
    const data = error.response?.data as ErrorResponse;

    // Try to get detailed error message from response
    if (data?.detail) return data.detail;
    if (data?.message) return data.message;
    if (data?.error) return data.error;

    // Fallback to status-based messages
    if (error.response) {
      switch (error.response.status) {
        case 400:
          return 'Bad request - please check your input';
        case 401:
          return 'Unauthorized - please authenticate';
        case 403:
          return 'Forbidden - you do not have permission';
        case 404:
          return 'Resource not found';
        case 408:
          return 'Request timeout - please try again';
        case 429:
          return 'Too many requests - please slow down';
        case 500:
          return 'Server error - please try again later';
        case 502:
          return 'Bad gateway - server is unreachable';
        case 503:
          return 'Service unavailable - please try again later';
        default:
          return `Server error (${error.response.status})`;
      }
    }

    // Network errors
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout - please try again';
    }
    if (error.code === 'ERR_NETWORK') {
      return 'Network error - please check your connection';
    }

    // Fallback to error message
    if (error.message) return error.message;
  }

  // Handle standard Error objects
  if (error instanceof Error) {
    return error.message;
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }

  // Fallback for unknown error types
  return 'An unexpected error occurred';
};

/**
 * Log error details for debugging
 */
export const logError = (context: string, error: unknown): void => {
  console.error(`[${context}]`, error);

  if (error instanceof AxiosError) {
    console.error('Request:', {
      url: error.config?.url,
      method: error.config?.method,
      data: error.config?.data,
    });
    console.error('Response:', {
      status: error.response?.status,
      data: error.response?.data,
    });
  }
};

/**
 * Retry configuration for failed requests
 */
export interface RetryConfig {
  maxAttempts: number;
  delayMs: number;
  backoff?: boolean;
}

/**
 * Retry a function with exponential backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  config: RetryConfig = { maxAttempts: 3, delayMs: 1000, backoff: true }
): Promise<T> => {
  let lastError: unknown;

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt < config.maxAttempts) {
        const delay = config.backoff
          ? config.delayMs * Math.pow(2, attempt - 1)
          : config.delayMs;

        console.log(`Retry attempt ${attempt}/${config.maxAttempts} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
};