'use client';

import { FileCode, Code2, Clock, GitBranch, Package, Server } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAppStore } from '@/lib/store';
import { mockProjects, mockArchitectureReport } from '@/lib/mock-data';

export function OverviewTab() {
  const { currentProjectId, projects } = useAppStore();

  // Get current project or use mock
  const allProjects = projects.length > 0 ? projects : mockProjects;
  const currentProject = allProjects.find(p => p.id === currentProjectId) || mockProjects[0];
  const report = mockArchitectureReport;

  return (
    <div className="p-6 space-y-6">
      {/* Project Info Header */}
      <div>
        <h1 className="text-2xl font-bold">{currentProject?.name || report.overview.name}</h1>
        <p className="text-muted-foreground mt-1">{report.overview.description}</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <FileCode className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{report.overview.stats.files}</p>
                <p className="text-sm text-muted-foreground">Files</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <Code2 className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{(report.overview.stats.linesOfCode / 1000).toFixed(1)}k</p>
                <p className="text-sm text-muted-foreground">Lines of Code</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                <Package className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{report.dependencies.external.length}</p>
                <p className="text-sm text-muted-foreground">Dependencies</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <Clock className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{report.overview.stats.directories}</p>
                <p className="text-sm text-muted-foreground">Directories</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Tech Stack */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Tech Stack
            </CardTitle>
            <CardDescription>Technologies detected in this project</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Languages</p>
              <div className="flex flex-wrap gap-2">
                {report.techStack.languages.map((lang) => (
                  <Badge key={lang} variant="secondary">{lang}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Frameworks</p>
              <div className="flex flex-wrap gap-2">
                {report.techStack.frameworks.map((fw) => (
                  <Badge key={fw} variant="secondary">{fw}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Databases</p>
              <div className="flex flex-wrap gap-2">
                {report.techStack.databases.map((db) => (
                  <Badge key={db} variant="secondary">{db}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Tools</p>
              <div className="flex flex-wrap gap-2">
                {report.techStack.tools.map((tool) => (
                  <Badge key={tool} variant="outline">{tool}</Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Key Files */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCode className="h-5 w-5" />
              Key Files
            </CardTitle>
            <CardDescription>Important files in this codebase</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {report.keyFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                >
                  <FileCode className="h-4 w-4 mt-0.5 text-muted-foreground" />
                  <div>
                    <p className="font-mono text-sm">{file.file}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{file.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Architecture & Entry Points */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Architecture Pattern
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="default" className="text-sm py-1 px-3">
              {report.architecturePattern}
            </Badge>
            <p className="text-sm text-muted-foreground mt-3">
              This codebase follows a layered architecture pattern with clear separation between
              API routes, services, and data models.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code2 className="h-5 w-5" />
              Entry Points
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {report.entryPoints.map((entry, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono text-xs">
                    {entry.file}
                  </Badge>
                  <span className="text-sm text-muted-foreground">{entry.description}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Languages Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Languages Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(report.overview.stats.languages).map(([lang, stats]) => {
              const percentage = (stats.lines / report.overview.stats.linesOfCode) * 100;
              return (
                <div key={lang}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">{lang}</span>
                    <span className="text-muted-foreground">
                      {stats.files} files, {(stats.lines / 1000).toFixed(1)}k lines
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
