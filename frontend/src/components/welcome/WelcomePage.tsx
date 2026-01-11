'use client';

import { useState } from 'react';
import { Compass, GitBranch, Folder, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAppStore } from '@/lib/store';
import { HealthCheck } from '@/components/debug/HealthCheck';

export function WelcomePage() {
  const { addProject, setAnalysisProgress } = useAppStore();
  const [gitUrl, setGitUrl] = useState('');
  const [gitBranch, setGitBranch] = useState('main');
  const [localPath, setLocalPath] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleGitSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!gitUrl.trim()) return;

    setIsLoading(true);

    // Extract repo name from URL
    const repoName = gitUrl.split('/').pop()?.replace('.git', '') || 'project';

    // Create new project
    const newProject = {
      id: Date.now().toString(),
      name: repoName,
      sourceType: 'git_url' as const,
      source: gitUrl,
      branch: gitBranch || 'main',
      status: 'cloning' as const,
      createdAt: new Date().toISOString(),
    };

    addProject(newProject);

    // Start mock analysis progress
    setAnalysisProgress({
      currentStep: 'cloning',
      overallPercent: 0,
    });

    setIsLoading(false);
  };

  const handleLocalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!localPath.trim()) return;

    setIsLoading(true);

    // Extract folder name from path
    const folderName = localPath.split('/').pop() || 'project';

    // Create new project
    const newProject = {
      id: Date.now().toString(),
      name: folderName,
      sourceType: 'local_path' as const,
      source: localPath,
      branch: 'local',
      status: 'scanning' as const,
      createdAt: new Date().toISOString(),
    };

    addProject(newProject);

    // Start mock analysis progress
    setAnalysisProgress({
      currentStep: 'scanning',
      overallPercent: 0,
    });

    setIsLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] p-8">
      <div className="w-full max-w-2xl">
        {/* Hero */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Compass className="h-12 w-12 text-primary" />
            <h1 className="text-4xl font-bold">CodeCompass</h1>
          </div>
          <p className="text-lg text-muted-foreground">
            Navigate and understand any codebase with AI-powered analysis
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <h3 className="font-medium text-sm">Architecture Reports</h3>
            <p className="text-xs text-muted-foreground mt-1">Auto-generated documentation</p>
          </div>
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h3 className="font-medium text-sm">Visual Diagrams</h3>
            <p className="text-xs text-muted-foreground mt-1">Mermaid architecture views</p>
          </div>
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-2">
              <svg className="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h3 className="font-medium text-sm">AI Q&A Chat</h3>
            <p className="text-xs text-muted-foreground mt-1">Ask questions about code</p>
          </div>
        </div>

        {/* Onboarding Form */}
        <Card>
          <CardHeader>
            <CardTitle>Add a Project</CardTitle>
            <CardDescription>
              Enter a Git repository URL or local path to start analyzing
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="git" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="git" className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4" />
                  Git Repository
                </TabsTrigger>
                <TabsTrigger value="local" className="flex items-center gap-2">
                  <Folder className="h-4 w-4" />
                  Local Path
                </TabsTrigger>
              </TabsList>

              <TabsContent value="git" className="mt-4">
                <form onSubmit={handleGitSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="git-url">Repository URL</Label>
                    <Input
                      id="git-url"
                      placeholder="https://github.com/user/repo.git"
                      value={gitUrl}
                      onChange={(e) => setGitUrl(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="git-branch">Branch (optional)</Label>
                    <Input
                      id="git-branch"
                      placeholder="main"
                      value={gitBranch}
                      onChange={(e) => setGitBranch(e.target.value)}
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={!gitUrl.trim() || isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        Analyze Repository
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="local" className="mt-4">
                <form onSubmit={handleLocalSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="local-path">Local Path</Label>
                    <Input
                      id="local-path"
                      placeholder="/home/user/projects/my-app"
                      value={localPath}
                      onChange={(e) => setLocalPath(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Enter the absolute path to your project folder
                    </p>
                  </div>
                  <Button type="submit" className="w-full" disabled={!localPath.trim() || isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        Analyze Project
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* API Health Check (Debug) */}
        <div className="mt-6 max-w-md mx-auto">
          <HealthCheck />
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          Supports Python and JavaScript/TypeScript projects
        </p>
      </div>
    </div>
  );
}
