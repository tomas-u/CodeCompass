/**
 * Loading Skeleton Components
 *
 * Skeleton screens for various loading states
 */

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

/**
 * Project card skeleton (for project list)
 */
export function ProjectCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2 mt-2" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Project list skeleton
 */
export function ProjectListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <ProjectCardSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * Dashboard overview skeleton
 */
export function DashboardSkeleton() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96 mt-2" />
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded-lg" />
                <div className="flex-1">
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-4 w-20 mt-1" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Content cards */}
      <div className="grid grid-cols-2 gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-64 mt-2" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, j) => (
                  <Skeleton key={j} className="h-4 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/**
 * File tree skeleton
 */
export function FileTreeSkeleton() {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} style={{ paddingLeft: `${(i % 3) * 16}px` }}>
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Report skeleton
 */
export function ReportSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-4/6" />
      <div className="mt-6 space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    </div>
  );
}

/**
 * Chat message skeleton
 */
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />}
      <div className="space-y-2 max-w-[85%]">
        <Skeleton className="h-20 w-80 rounded-lg" />
      </div>
      {isUser && <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />}
    </div>
  );
}

/**
 * Generic loading spinner
 */
export function LoadingSpinner({ size = 'default' }: { size?: 'sm' | 'default' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className="flex items-center justify-center p-8">
      <div className={`animate-spin rounded-full border-4 border-muted border-t-primary ${sizeClasses[size]}`} />
    </div>
  );
}

/**
 * Full page loading
 */
export function FullPageLoading({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full border-4 border-muted border-t-primary h-12 w-12" />
      {message && <p className="mt-4 text-muted-foreground">{message}</p>}
    </div>
  );
}

/**
 * Project header skeleton
 */
export function ProjectHeaderSkeleton() {
  return (
    <div className="border-b border-border bg-background px-6 py-4">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Back button and title */}
          <div className="flex items-center gap-3 mb-2">
            <Skeleton className="h-8 w-8" />
            <div className="flex items-center gap-3">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
          </div>
          {/* Project metadata */}
          <div className="flex items-center gap-4 ml-11">
            <Skeleton className="h-4 w-64" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
        {/* Action Buttons and Stats */}
        <div className="ml-4 flex items-center gap-3">
          <Skeleton className="h-10 w-28" />
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-6">
                <div>
                  <Skeleton className="h-4 w-10" />
                  <Skeleton className="h-6 w-12 mt-1" />
                </div>
                <div>
                  <Skeleton className="h-4 w-10" />
                  <Skeleton className="h-6 w-12 mt-1" />
                </div>
                <div>
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-6 w-8 mt-1" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

/**
 * Project page skeleton (header + dashboard)
 */
export function ProjectPageSkeleton() {
  return (
    <div className="h-full flex flex-col">
      <ProjectHeaderSkeleton />
      <div className="flex-1 overflow-hidden">
        <DashboardSkeleton />
      </div>
    </div>
  );
}

/**
 * Content loading placeholder - shows while analysis is in progress
 */
export function ContentLoading({ message = 'Loading data...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
      <div className="animate-spin rounded-full border-4 border-muted border-t-primary h-8 w-8 mb-4" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

/**
 * Analysis steps with icons and descriptions
 */
const analysisSteps = [
  { id: 'pending', label: 'Preparing', description: 'Setting up analysis...' },
  { id: 'cloning', label: 'Cloning Repository', description: 'Downloading source code...' },
  { id: 'scanning', label: 'Scanning Files', description: 'Identifying code files...' },
  { id: 'analyzing', label: 'Analyzing Code', description: 'Understanding code structure...' },
  { id: 'generating', label: 'Generating Reports', description: 'Creating documentation...' },
  { id: 'indexing', label: 'Building Index', description: 'Indexing for Q&A...' },
];

/**
 * Analysis in progress placeholder - shows step-by-step progress
 */
export function AnalysisInProgress({ status }: { status: string }) {
  // Map status to step index (some statuses map to the same step)
  const getStepIndex = (s: string) => {
    const index = analysisSteps.findIndex(step => step.id === s);
    return index >= 0 ? index : 0;
  };

  const currentStepIndex = getStepIndex(status);
  const currentStep = analysisSteps[currentStepIndex];

  return (
    <div className="flex flex-col items-center justify-center py-12">
      {/* Current step message */}
      <div className="flex items-center gap-3 mb-6">
        <div className="animate-spin rounded-full border-4 border-muted border-t-primary h-8 w-8" />
        <div>
          <p className="text-sm font-medium">{currentStep.label}</p>
          <p className="text-xs text-muted-foreground">{currentStep.description}</p>
        </div>
      </div>

      {/* Step indicators */}
      <div className="flex items-center gap-2 mb-4">
        {analysisSteps.map((step, index) => {
          const isComplete = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;

          return (
            <div
              key={step.id}
              className={`w-2.5 h-2.5 rounded-full transition-all ${
                isComplete
                  ? 'bg-green-500'
                  : isCurrent
                  ? 'bg-primary animate-pulse'
                  : 'bg-muted'
              }`}
              title={step.label}
            />
          );
        })}
      </div>

      {/* Progress text */}
      <p className="text-xs text-muted-foreground">
        Step {currentStepIndex + 1} of {analysisSteps.length}
      </p>
    </div>
  );
}

/**
 * Project dropdown skeleton (for Header dropdown)
 */
export function ProjectDropdownSkeleton({ count = 2 }: { count?: number }) {
  return (
    <div className="p-2 space-y-1">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="px-2 py-2 space-y-1">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-48" />
        </div>
      ))}
    </div>
  );
}
