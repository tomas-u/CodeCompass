/**
 * Error Message Component
 *
 * Displays user-friendly error messages with optional retry action
 */

import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { getErrorMessage, isApiError, isNetworkError, isTimeoutError } from '@/lib/api-error';

interface ErrorMessageProps {
  error: unknown;
  onRetry?: () => void;
  title?: string;
  className?: string;
}

export function ErrorMessage({ error, onRetry, title, className }: ErrorMessageProps) {
  const message = getErrorMessage(error);

  // Determine error type for better UX
  const isNetwork = isNetworkError(error);
  const isTimeout = isTimeoutError(error);
  const showRetry = onRetry && (isNetwork || isTimeout || (isApiError(error) && error.isServerError()));

  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title || 'Error'}</AlertTitle>
      <AlertDescription className="mt-2">
        <p>{message}</p>
        {showRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="mt-3"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

/**
 * Inline error message (smaller, for form fields or cards)
 */
export function InlineError({ error, onRetry }: ErrorMessageProps) {
  const message = getErrorMessage(error);

  return (
    <div className="flex items-center gap-2 text-sm text-destructive">
      <AlertCircle className="h-4 w-4 flex-shrink-0" />
      <span>{message}</span>
      {onRetry && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onRetry}
          className="h-6 px-2 ml-auto"
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
}

/**
 * Full-page error (for critical failures)
 */
export function FullPageError({ error, onRetry }: ErrorMessageProps) {
  const message = getErrorMessage(error);

  return (
    <div className="flex items-center justify-center min-h-screen p-8">
      <div className="text-center max-w-md">
        <AlertCircle className="h-16 w-16 text-destructive mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>
        <p className="text-muted-foreground mb-6">{message}</p>
        {onRetry && (
          <Button onClick={onRetry} size="lg">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        )}
      </div>
    </div>
  );
}
