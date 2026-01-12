'use client';

import { Compass, ChevronDown, Settings, HelpCircle, Plus, Check, Loader2, FolderOpen, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useAppStore } from '@/lib/store';

export function Header() {
  const { currentProjectId, setCurrentProject, projects, isLoadingProjects, projectsError } = useAppStore();

  const currentProject = projects.find(p => p.id === currentProjectId);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <Badge variant="default" className="bg-green-600 text-xs"><Check className="w-3 h-3 mr-1" />Ready</Badge>;
      case 'analyzing':
        return <Badge variant="secondary" className="text-xs"><Loader2 className="w-3 h-3 mr-1 animate-spin" />Analyzing</Badge>;
      default:
        return <Badge variant="outline" className="text-xs">{status}</Badge>;
    }
  };

  return (
    <header className="h-14 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 fixed top-0 left-0 right-0 z-50">
      <div className="flex items-center justify-between h-full px-4">
        {/* Logo */}
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setCurrentProject(null)}>
          <Compass className="h-6 w-6 text-primary" />
          <span className="font-semibold text-lg">CodeCompass</span>
        </div>

        {/* Project Selector */}
        <div className="flex-1 flex justify-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="min-w-[200px] justify-between">
                <span className="flex items-center gap-2">
                  <FolderOpen className="h-4 w-4" />
                  {currentProject ? currentProject.name : 'Select Project'}
                </span>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-[300px]">
              {isLoadingProjects && (
                <div className="flex items-center justify-center p-4">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Loading projects...</span>
                </div>
              )}

              {projectsError && (
                <div className="p-4">
                  <div className="flex items-center gap-2 text-destructive mb-2">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Error loading projects</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{projectsError}</p>
                </div>
              )}

              {!isLoadingProjects && !projectsError && projects.length === 0 && (
                <DropdownMenuLabel className="font-normal text-muted-foreground">
                  No projects yet
                </DropdownMenuLabel>
              )}

              {!isLoadingProjects && !projectsError && projects.map((project) => (
                <DropdownMenuItem
                  key={project.id}
                  onClick={() => setCurrentProject(project.id)}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{project.name}</span>
                    <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                      {project.source}
                    </span>
                  </div>
                  {getStatusBadge(project.status)}
                </DropdownMenuItem>
              ))}

              {!isLoadingProjects && projects.length > 0 && <DropdownMenuSeparator />}
              <DropdownMenuItem
                onClick={() => setCurrentProject(null)}
                className="cursor-pointer"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add New Project
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}
