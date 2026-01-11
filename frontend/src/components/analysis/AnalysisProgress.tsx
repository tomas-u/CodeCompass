'use client';

import { useEffect, useState } from 'react';
import { GitBranch, Search, Brain, FileCode, Database, Check, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useAppStore } from '@/lib/store';

const steps = [
  { id: 'cloning', label: 'Cloning Repository', icon: GitBranch, description: 'Downloading source code...' },
  { id: 'scanning', label: 'Scanning Files', icon: Search, description: 'Identifying code files...' },
  { id: 'analyzing', label: 'Analyzing Code', icon: Brain, description: 'Understanding code structure...' },
  { id: 'generating', label: 'Generating Reports', icon: FileCode, description: 'Creating documentation...' },
  { id: 'indexing', label: 'Building Index', icon: Database, description: 'Indexing for Q&A...' },
];

export function AnalysisProgress() {
  const { analysisProgress, setAnalysisProgress, projects, currentProjectId } = useAppStore();
  const [mockProgress, setMockProgress] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const currentProject = projects.find(p => p.id === currentProjectId);

  // Simulate progress for MVP
  useEffect(() => {
    if (!analysisProgress) return;

    const interval = setInterval(() => {
      setMockProgress(prev => {
        const newProgress = prev + Math.random() * 3;

        if (newProgress >= 100) {
          clearInterval(interval);
          // Complete the analysis
          setTimeout(() => {
            setAnalysisProgress(null);
          }, 500);
          return 100;
        }

        // Update step based on progress
        const stepThresholds = [20, 40, 60, 80, 100];
        const newStepIndex = stepThresholds.findIndex(threshold => newProgress < threshold);
        if (newStepIndex !== currentStepIndex && newStepIndex !== -1) {
          setCurrentStepIndex(newStepIndex);
          setAnalysisProgress({
            ...analysisProgress,
            currentStep: steps[newStepIndex].id as any,
            overallPercent: Math.round(newProgress),
          });
        }

        return newProgress;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [analysisProgress]);

  if (!analysisProgress) return null;

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            Analyzing Project
          </CardTitle>
          <CardDescription>
            {currentProject?.name || 'Project'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Progress */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Overall Progress</span>
              <span className="font-medium">{Math.round(mockProgress)}%</span>
            </div>
            <Progress value={mockProgress} className="h-2" />
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {steps.map((step, index) => {
              const isComplete = index < currentStepIndex;
              const isCurrent = index === currentStepIndex;
              const isPending = index > currentStepIndex;
              const StepIcon = step.icon;

              return (
                <div
                  key={step.id}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    isCurrent ? 'bg-primary/10' : isComplete ? 'bg-muted/50' : 'opacity-50'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isComplete
                        ? 'bg-green-500 text-white'
                        : isCurrent
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    {isComplete ? (
                      <Check className="h-4 w-4" />
                    ) : isCurrent ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <StepIcon className="h-4 w-4" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`font-medium text-sm ${isPending ? 'text-muted-foreground' : ''}`}>
                      {step.label}
                    </p>
                    {isCurrent && (
                      <p className="text-xs text-muted-foreground">{step.description}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Current file being processed */}
          {analysisProgress.currentFile && (
            <div className="text-center">
              <p className="text-xs text-muted-foreground truncate">
                Processing: {analysisProgress.currentFile}
              </p>
            </div>
          )}

          {/* Stats */}
          {analysisProgress.filesProcessed !== undefined && (
            <div className="flex justify-center gap-6 text-sm">
              <div className="text-center">
                <p className="font-medium">{analysisProgress.filesProcessed}</p>
                <p className="text-xs text-muted-foreground">Files Processed</p>
              </div>
              {analysisProgress.filesTotal !== undefined && (
                <div className="text-center">
                  <p className="font-medium">{analysisProgress.filesTotal}</p>
                  <p className="text-xs text-muted-foreground">Total Files</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
