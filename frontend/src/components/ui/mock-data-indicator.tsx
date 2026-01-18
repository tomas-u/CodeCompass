'use client';

import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MockDataIndicatorProps {
  children: React.ReactNode;
  label?: string;
  className?: string;
  /** Show as subtle border only (default) or prominent overlay */
  variant?: 'border' | 'overlay';
}

/**
 * Wraps components that use mock data with a visual indicator.
 * Only visible in development mode.
 *
 * Use this to highlight areas that still need backend integration.
 */
export function MockDataIndicator({
  children,
  label = 'Mock Data',
  className,
  variant = 'border'
}: MockDataIndicatorProps) {
  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return <>{children}</>;
  }

  if (variant === 'overlay') {
    return (
      <div className={cn('relative', className)}>
        {/* Red tint overlay */}
        <div className="absolute inset-0 bg-red-500/5 pointer-events-none rounded-lg z-10" />

        {/* Label badge */}
        <div className="absolute top-2 right-2 z-20 flex items-center gap-1 px-2 py-1 bg-red-500/90 text-white text-xs font-medium rounded-md shadow-sm">
          <AlertTriangle className="h-3 w-3" />
          {label}
        </div>

        {children}
      </div>
    );
  }

  // Border variant (default) - more subtle
  return (
    <div
      className={cn(
        'relative rounded-lg ring-2 ring-red-400/50 ring-offset-2 ring-offset-background',
        className
      )}
    >
      {/* Label badge */}
      <div className="absolute -top-3 left-3 z-20 flex items-center gap-1 px-2 py-0.5 bg-red-500 text-white text-xs font-medium rounded shadow-sm">
        <AlertTriangle className="h-3 w-3" />
        {label}
      </div>

      {children}
    </div>
  );
}

/**
 * Inline indicator for smaller mock data sections
 */
export function MockDataBadge({ label = 'Mock' }: { label?: string }) {
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-red-500/10 text-red-600 text-xs font-medium rounded border border-red-300">
      <AlertTriangle className="h-3 w-3" />
      {label}
    </span>
  );
}
