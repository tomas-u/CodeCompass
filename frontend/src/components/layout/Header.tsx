'use client';

import { useState } from 'react';
import { Compass, ChevronDown, Settings, HelpCircle, Plus, Check, Loader2, FolderOpen, MessageSquare } from 'lucide-react';
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
import { ProjectDropdownSkeleton } from '@/components/ui/loading-skeleton';
import { InlineError } from '@/components/ui/error-message';
import { LLMStatusIndicator } from './LLMStatusIndicator';
import { SettingsDialog, type SettingsTab } from '@/components/settings/SettingsDialog';

export function Header() {
  const {
    currentProjectId, setCurrentProject, projects, isLoadingProjects,
    projectsError, fetchProjects, isChatPanelOpen, toggleChatPanel,
    llmConfig, llmStatus, llmError,
  } = useAppStore();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsTab, setSettingsTab] = useState<SettingsTab>('llm');

  const currentProject = projects.find(p => p.id === currentProjectId);

  const handleStatusClick = () => {
    setSettingsTab('llm');
    setSettingsOpen(true);
  };

  const handleSettingsClick = () => {
    setSettingsOpen(true);
  };

  // Map store config to LLMStatusIndicator props
  const indicatorConfig = llmConfig ? {
    providerType: llmConfig.provider_type,
    model: llmConfig.model,
    status: llmStatus,
    baseUrl: llmConfig.base_url,
  } : undefined;

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
              {isLoadingProjects && <ProjectDropdownSkeleton count={2} />}

              {projectsError && (
                <div className="p-3">
                  <InlineError error={projectsError} onRetry={fetchProjects} />
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
                  data-testid="project-item"
                  data-status={project.status}
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
          {/* LLM Status Indicator */}
          <LLMStatusIndicator
            onClick={handleStatusClick}
            config={indicatorConfig}
            error={llmError}
          />

          {/* Chat toggle - only shown when a project is selected */}
          {currentProjectId && (
            <Button
              variant={isChatPanelOpen ? "default" : "ghost"}
              size="icon"
              onClick={toggleChatPanel}
              title={isChatPanelOpen ? "Close chat panel" : "Open chat panel"}
            >
              <MessageSquare className="h-5 w-5" />
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={handleSettingsClick} title="Settings">
            <Settings className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-5 w-5" />
          </Button>
        </div>

        {/* Settings Dialog */}
        <SettingsDialog
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          defaultTab={settingsTab}
        />
      </div>
    </header>
  );
}
