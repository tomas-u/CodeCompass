/**
 * API Error Handling
 *
 * Custom error class and utilities for handling API errors
 */

import { ErrorResponse } from '@/types/api';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  code: string;
  statusCode: number;
  details?: any;
  requestId?: string;

  constructor(
    message: string,
    code: string,
    statusCode: number,
    details?: any,
    requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.requestId = requestId;

    // Maintains proper stack trace for where our error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }

  /**
   * Create ApiError from backend error response
   */
  static fromResponse(response: ErrorResponse, statusCode: number): ApiError {
    return new ApiError(
      response.error.message,
      response.error.code,
      statusCode,
      response.error.details,
      response.request_id
    );
  }

  /**
   * Check if error is a specific type
   */
  is(code: string): boolean {
    return this.code === code;
  }

  /**
   * Check if error is a client error (4xx)
   */
  isClientError(): boolean {
    return this.statusCode >= 400 && this.statusCode < 500;
  }

  /**
   * Check if error is a server error (5xx)
   */
  isServerError(): boolean {
    return this.statusCode >= 500;
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(): string {
    // Map error codes to user-friendly messages
    const userMessages: Record<string, string> = {
      PROJECT_NOT_FOUND: 'Project not found',
      ANALYSIS_NOT_FOUND: 'Analysis not found',
      REPORT_NOT_FOUND: 'Report not found',
      INVALID_GIT_URL: 'Invalid Git repository URL',
      PATH_NOT_FOUND: 'Local path does not exist',
      DUPLICATE_PROJECT: 'A project with this source already exists',
      ANALYSIS_IN_PROGRESS: 'Analysis is already running for this project',
      LLM_UNAVAILABLE: 'AI service is currently unavailable',
      VALIDATION_ERROR: 'Invalid input data',
    };

    return userMessages[this.code] || this.message || 'An unexpected error occurred';
  }
}

/**
 * Network error (no response from server)
 */
export class NetworkError extends Error {
  constructor(message: string = 'Unable to connect to the server') {
    super(message);
    this.name = 'NetworkError';

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, NetworkError);
    }
  }

  getUserMessage(): string {
    return 'Unable to connect to the server. Please check your internet connection.';
  }
}

/**
 * Timeout error
 */
export class TimeoutError extends Error {
  constructor(message: string = 'Request timed out') {
    super(message);
    this.name = 'TimeoutError';

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, TimeoutError);
    }
  }

  getUserMessage(): string {
    return 'The request took too long to complete. Please try again.';
  }
}

/**
 * Check if error is an ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

/**
 * Check if error is a NetworkError
 */
export function isNetworkError(error: unknown): error is NetworkError {
  return error instanceof NetworkError;
}

/**
 * Check if error is a TimeoutError
 */
export function isTimeoutError(error: unknown): error is TimeoutError {
  return error instanceof TimeoutError;
}

/**
 * Get user-friendly error message from any error
 */
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.getUserMessage();
  }

  if (isNetworkError(error) || isTimeoutError(error)) {
    return error.getUserMessage();
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred';
}

/**
 * Log error to console (in development) or error tracking service (in production)
 */
export function logError(error: unknown, context?: string): void {
  if (process.env.NODE_ENV === 'development') {
    console.error(`[API Error]${context ? ` ${context}` : ''}:`, error);
  } else {
    // In production, send to error tracking service (e.g., Sentry)
    // For now, just log to console
    console.error(`[API Error]${context ? ` ${context}` : ''}:`, error);
  }
}
