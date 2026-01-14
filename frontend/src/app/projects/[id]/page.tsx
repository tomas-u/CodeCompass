'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, GitBranch, FolderGit, Clock, Check, Loader2, AlertCircle, PlayCircle, AlertTriangle } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/components/dashboard/Dashboard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAppStore } from '@/lib/store';
import { api } from '@/lib/api';
import { getErrorMessage } from '@/lib/api-error';
import { ErrorMessage } from '@/components/ui/error-message';
import { FullPageLoading } from '@/components/ui/loading-skeleton';
import { useProjectStatus } from '@/hooks/useProjectStatus';
import type { Project } from '@/types/api';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const { setCurrentProject, currentProjectId } = useAppStore();
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState<number | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [isStartingAnalysis, setIsStartingAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Fetch project data
  useEffect(() => {
    const fetchProject = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await api.getProject(projectId);
        setProject(data);

        // Set as current project in store
        if (currentProjectId !== projectId) {
          setCurrentProject(projectId);
        }
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };

    fetchProject();
  }, [projectId, setCurrentProject, currentProjectId]);

  // Poll project status when project is being analyzed
  const activeStates = ['analyzing', 'scanning', 'cloning', 'pending'];
  const shouldPoll = project && activeStates.includes(project.status);

  useProjectStatus({
    projectId,
    onStatusUpdate: (updatedProject) => {
      // Merge updated fields into current project state
      setProject((prev) => {
        if (!prev) return prev;
        const updated = { ...prev, ...updatedProject };

        // Also update the project in the Zustand store to keep list in sync
        const { projects, setProjects } = useAppStore.getState();
        const updatedProjects = projects.map((p) =>
          p.id === projectId ? updated : p
        );
        setProjects(updatedProjects);

        return updated;
      });
    },
    onAnalysisUpdate: (analysis) => {
      // Update progress percentage if available
      if (analysis.progress !== undefined) {
        setAnalysisProgress(analysis.progress);
      }
    },
    onError: (errorMessage) => {
      console.error('Polling error:', errorMessage);
      // Don't set error state - polling will retry
    },
    enabled: shouldPoll,
  });

  // Handle analysis trigger
  const handleStartAnalysis = async () => {
    setAnalysisError(null);
    setIsStartingAnalysis(true);

    try {
      await api.startAnalysis(projectId, {
        force: false,
        generate_reports: true,
        generate_diagrams: true,
        build_embeddings: true,
      });

      // Close dialog
      setShowConfirmDialog(false);

      // Refetch project to get updated status
      const updatedProject = await api.getProject(projectId);
      setProject(updatedProject);

      // Update in store as well
      const { projects, setProjects } = useAppStore.getState();
      const updatedProjects = projects.map((p) =>
        p.id === projectId ? updatedProject : p
      );
      setProjects(updatedProjects);
    } catch (err) {
      setAnalysisError(getErrorMessage(err));
    } finally {
      setIsStartingAnalysis(false);
    }
  };

  // Check if analysis can be started
  const canStartAnalysis = project && !activeStates.includes(project.status);

  // Loading state
  if (isLoading) {
    return (
      <MainLayout>
        <FullPageLoading message="Loading project..." />
      </MainLayout>
    );
  }

  // Error state
  if (error || !project) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] p-8">
          <div className="w-full max-w-md">
            <ErrorMessage
              error={error || 'Project not found'}
              onRetry={() => window.location.reload()}
              title="Failed to load project"
            />
            <Button
              variant="outline"
              className="w-full mt-4"
              onClick={() => router.push('/')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  // Get status badge
  const getStatusBadge = () => {
    switch (project.status) {
      case 'ready':
        return (
          <Badge variant="default" className="bg-green-600">
            <Check className="w-3 h-3 mr-1" />
            Ready
          </Badge>
        );
      case 'analyzing':
      case 'scanning':
      case 'cloning':
        return (
          <Badge variant="secondary">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive">
            <AlertCircle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
        );
      case 'pending':
      default:
        return (
          <Badge variant="outline">
            <Clock className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        );
    }
  };

  // Get source icon
  const SourceIcon = project.source_type === 'git_url' ? GitBranch : FolderGit;

  return (
    <MainLayout>
      <div className="h-full flex flex-col">
        {/* Project Header */}
        <div className="border-b border-border bg-background px-6 py-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              {/* Back button and title */}
              <div className="flex items-center gap-3 mb-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/')}
                  className="h-8"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold truncate">{project.name}</h1>
                  {getStatusBadge()}
                  {analysisProgress !== null && activeStates.includes(project.status) && (
                    <span className="text-sm text-muted-foreground">
                      {Math.round(analysisProgress)}% complete
                    </span>
                  )}
                </div>
              </div>

              {/* Project metadata */}
              <div className="flex items-center gap-4 text-sm text-muted-foreground ml-11">
                <div className="flex items-center gap-1.5">
                  <SourceIcon className="h-4 w-4" />
                  <span className="truncate max-w-md">{project.source}</span>
                </div>
                {project.branch && project.source_type === 'git_url' && (
                  <>
                    <Separator orientation="vertical" className="h-4" />
                    <span>Branch: {project.branch}</span>
                  </>
                )}
                {project.last_analyzed_at && (
                  <>
                    <Separator orientation="vertical" className="h-4" />
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-4 w-4" />
                      Last analyzed: {new Date(project.last_analyzed_at).toLocaleString()}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Action Buttons and Stats */}
            <div className="ml-4 flex items-center gap-3">
              {/* Analyze Button */}
              <Button
                onClick={() => setShowConfirmDialog(true)}
                disabled={!canStartAnalysis}
                variant={canStartAnalysis ? "default" : "outline"}
                className="h-10"
              >
                <PlayCircle className="h-4 w-4 mr-2" />
                {activeStates.includes(project.status) ? 'Analyzing...' : 'Analyze'}
              </Button>

              {/* Stats Summary */}
              {project.stats && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-6 text-sm">
                      {project.stats.files !== undefined && (
                        <div>
                          <p className="text-muted-foreground">Files</p>
                          <p className="text-lg font-semibold">{project.stats.files.toLocaleString()}</p>
                        </div>
                      )}
                      {project.stats.lines_of_code !== undefined && (
                        <div>
                          <p className="text-muted-foreground">Lines</p>
                          <p className="text-lg font-semibold">
                            {(project.stats.lines_of_code / 1000).toFixed(1)}k
                          </p>
                        </div>
                      )}
                      {project.stats.languages && Object.keys(project.stats.languages).length > 0 && (
                        <div>
                          <p className="text-muted-foreground">Languages</p>
                          <p className="text-lg font-semibold">{Object.keys(project.stats.languages).length}</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Description */}
          {project.description && (
            <p className="text-sm text-muted-foreground mt-3 ml-11">{project.description}</p>
          )}
        </div>

        {/* Dashboard with Tabs */}
        <div className="flex-1 overflow-hidden">
          <Dashboard />
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Start Code Analysis?</DialogTitle>
            <DialogDescription>
              This will analyze the project's codebase, generate reports, create diagrams, and build embeddings for AI-powered Q&A.
              {project?.stats && (
                <span className="block mt-2 text-sm">
                  The project has {project.stats.files?.toLocaleString() || 0} files. Analysis may take a few minutes.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {/* Show error if analysis failed */}
          {analysisError && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Analysis Failed</AlertTitle>
              <AlertDescription>{analysisError}</AlertDescription>
            </Alert>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowConfirmDialog(false);
                setAnalysisError(null);
              }}
              disabled={isStartingAnalysis}
            >
              Cancel
            </Button>
            <Button
              onClick={handleStartAnalysis}
              disabled={isStartingAnalysis}
            >
              {isStartingAnalysis ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <PlayCircle className="h-4 w-4 mr-2" />
                  Start Analysis
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </MainLayout>
  );
}
