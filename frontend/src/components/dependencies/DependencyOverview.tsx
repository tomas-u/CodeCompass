'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  AlertTriangle,
  FileCode,
  GitBranch,
  ArrowDownToLine,
  ArrowUpFromLine,
  Search,
  Loader2,
  ChevronRight,
  ExternalLink,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { api } from '@/lib/api';
import type { DependencySummary, FileEgoGraph, FileDependencyInfo } from '@/types/api';

interface DependencyOverviewProps {
  projectId: string;
}

export function DependencyOverview({ projectId }: DependencyOverviewProps) {
  const [summary, setSummary] = useState<DependencySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // File search and selection
  const [searchQuery, setSearchQuery] = useState('');
  const [allFiles, setAllFiles] = useState<FileDependencyInfo[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);

  // Selected file ego graph
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [egoGraph, setEgoGraph] = useState<FileEgoGraph | null>(null);
  const [egoLoading, setEgoLoading] = useState(false);

  // Load summary data
  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDependencySummary(projectId);
      setSummary(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load dependency summary');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // Load file list for search
  const loadFiles = useCallback(async () => {
    setFilesLoading(true);
    try {
      const data = await api.getDependencyFiles(projectId);
      setAllFiles(data.files);
    } catch (err) {
      console.error('Failed to load files:', err);
    } finally {
      setFilesLoading(false);
    }
  }, [projectId]);

  // Load ego graph for selected file
  const loadEgoGraph = useCallback(async (filePath: string) => {
    setEgoLoading(true);
    setSelectedFile(filePath);
    try {
      const data = await api.getFileDependencies(projectId, filePath);
      setEgoGraph(data);
    } catch (err: any) {
      console.error('Failed to load file dependencies:', err);
      setEgoGraph(null);
    } finally {
      setEgoLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadSummary();
    loadFiles();
  }, [loadSummary, loadFiles]);

  // Filter files by search query
  const filteredFiles = searchQuery
    ? allFiles.filter(f =>
        f.file.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.module_name.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 20)
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading dependency analysis...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!summary) return null;

  return (
    <div className="space-y-4 p-1">
      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <FileCode className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Files</span>
            </div>
            <p className="text-2xl font-bold">{summary.stats.total_files}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Dependencies</span>
            </div>
            <p className="text-2xl font-bold">{summary.stats.total_dependencies}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <ArrowDownToLine className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Max Depth</span>
            </div>
            <p className="text-2xl font-bold">{summary.stats.max_depth}</p>
          </CardContent>
        </Card>
        <Card className={summary.circular_dependencies.has_circular ? 'border-amber-500' : ''}>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className={`h-4 w-4 ${summary.circular_dependencies.has_circular ? 'text-amber-500' : 'text-muted-foreground'}`} />
              <span className="text-sm text-muted-foreground">Circular</span>
            </div>
            <p className={`text-2xl font-bold ${summary.circular_dependencies.has_circular ? 'text-amber-500' : ''}`}>
              {summary.circular_dependencies.count}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left Column: Circular Dependencies + Top Files */}
        <div className="space-y-4">
          {/* Circular Dependencies */}
          {summary.circular_dependencies.has_circular && (
            <Card className="border-amber-500">
              <CardHeader className="py-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  Circular Dependencies
                </CardTitle>
                <CardDescription>
                  These files have circular import chains that may cause issues
                </CardDescription>
              </CardHeader>
              <CardContent className="py-2">
                <ScrollArea className="h-32">
                  {summary.circular_dependencies.cycles.map((cycle, i) => (
                    <div key={i} className="mb-2 p-2 bg-amber-50 dark:bg-amber-950/30 rounded text-sm">
                      <div className="flex items-center flex-wrap gap-1">
                        {cycle.files.map((file, j) => (
                          <span key={j} className="flex items-center">
                            <button
                              className="text-amber-700 dark:text-amber-400 hover:underline"
                              onClick={() => loadEgoGraph(file)}
                            >
                              {file.split('/').pop()}
                            </button>
                            {j < cycle.files.length - 1 && (
                              <ChevronRight className="h-3 w-3 mx-1 text-amber-500" />
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              </CardContent>
            </Card>
          )}

          {/* Most Imported Files */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-base flex items-center gap-2">
                <ArrowUpFromLine className="h-4 w-4" />
                Most Imported Files
              </CardTitle>
              <CardDescription>
                Critical files - changes here affect many others
              </CardDescription>
            </CardHeader>
            <CardContent className="py-2">
              <div className="space-y-1">
                {summary.most_imported.map((item, i) => (
                  <button
                    key={i}
                    className="w-full flex items-center justify-between p-2 hover:bg-muted rounded text-sm text-left"
                    onClick={() => loadEgoGraph(item.file)}
                  >
                    <span className="truncate flex-1 mr-2">{item.file}</span>
                    <span className="text-muted-foreground whitespace-nowrap">
                      {item.count} dependents
                    </span>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Most Dependencies */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-base flex items-center gap-2">
                <ArrowDownToLine className="h-4 w-4" />
                Most Dependencies
              </CardTitle>
              <CardDescription>
                Files that import the most other files
              </CardDescription>
            </CardHeader>
            <CardContent className="py-2">
              <div className="space-y-1">
                {summary.most_dependencies.map((item, i) => (
                  <button
                    key={i}
                    className="w-full flex items-center justify-between p-2 hover:bg-muted rounded text-sm text-left"
                    onClick={() => loadEgoGraph(item.file)}
                  >
                    <span className="truncate flex-1 mr-2">{item.file}</span>
                    <span className="text-muted-foreground whitespace-nowrap">
                      {item.count} imports
                    </span>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Search + Ego Graph */}
        <div className="space-y-4">
          {/* File Search */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Search className="h-4 w-4" />
                Explore File Dependencies
              </CardTitle>
              <CardDescription>
                Search for a file to see what it imports and what imports it
              </CardDescription>
            </CardHeader>
            <CardContent className="py-2">
              <div className="relative">
                <Input
                  placeholder="Search files..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pr-8"
                />
                {filesLoading && (
                  <Loader2 className="h-4 w-4 animate-spin absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
                )}
              </div>

              {/* Search Results */}
              {searchQuery && filteredFiles.length > 0 && (
                <ScrollArea className="h-40 mt-2 border rounded">
                  <div className="p-1">
                    {filteredFiles.map((file, i) => (
                      <button
                        key={i}
                        className="w-full flex items-center justify-between p-2 hover:bg-muted rounded text-sm text-left"
                        onClick={() => {
                          loadEgoGraph(file.file);
                          setSearchQuery('');
                        }}
                      >
                        <span className="truncate flex-1 mr-2">{file.file}</span>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {file.imports_count}↓ {file.imported_by_count}↑
                        </span>
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              )}

              {searchQuery && filteredFiles.length === 0 && !filesLoading && (
                <p className="text-sm text-muted-foreground mt-2 text-center py-4">
                  No files found matching "{searchQuery}"
                </p>
              )}
            </CardContent>
          </Card>

          {/* Ego Graph Display */}
          {selectedFile && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileCode className="h-4 w-4" />
                  <span className="truncate">{selectedFile.split('/').pop()}</span>
                  {egoGraph?.in_circular_dependency && (
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                  )}
                </CardTitle>
                <CardDescription className="truncate">
                  {selectedFile}
                </CardDescription>
              </CardHeader>
              <CardContent className="py-2">
                {egoLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : egoGraph ? (
                  <div className="space-y-4">
                    {/* Imports */}
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <ArrowDownToLine className="h-4 w-4" />
                        Imports ({egoGraph.imports_count})
                      </h4>
                      {egoGraph.imports.length > 0 ? (
                        <ScrollArea className="h-32">
                          <div className="space-y-1">
                            {egoGraph.imports.map((imp, i) => (
                              <button
                                key={i}
                                className="w-full flex items-center justify-between p-2 hover:bg-muted rounded text-sm text-left"
                                onClick={() => loadEgoGraph(imp.file)}
                              >
                                <span className="truncate">{imp.file}</span>
                                <span className="text-xs text-muted-foreground ml-2">
                                  {imp.language}
                                </span>
                              </button>
                            ))}
                          </div>
                        </ScrollArea>
                      ) : (
                        <p className="text-sm text-muted-foreground py-2">
                          No internal imports (leaf node)
                        </p>
                      )}
                    </div>

                    <Separator />

                    {/* Imported By */}
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <ArrowUpFromLine className="h-4 w-4" />
                        Imported By ({egoGraph.imported_by_count})
                      </h4>
                      {egoGraph.imported_by.length > 0 ? (
                        <ScrollArea className="h-32">
                          <div className="space-y-1">
                            {egoGraph.imported_by.map((dep, i) => (
                              <button
                                key={i}
                                className="w-full flex items-center justify-between p-2 hover:bg-muted rounded text-sm text-left"
                                onClick={() => loadEgoGraph(dep.file)}
                              >
                                <span className="truncate">{dep.file}</span>
                                <span className="text-xs text-muted-foreground ml-2">
                                  {dep.language}
                                </span>
                              </button>
                            ))}
                          </div>
                        </ScrollArea>
                      ) : (
                        <p className="text-sm text-muted-foreground py-2">
                          Not imported by any file (root node)
                        </p>
                      )}
                    </div>

                    {/* External Dependencies */}
                    {egoGraph.external_deps.length > 0 && (
                      <>
                        <Separator />
                        <div>
                          <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                            <ExternalLink className="h-4 w-4" />
                            External Dependencies ({egoGraph.external_deps.length})
                          </h4>
                          <div className="flex flex-wrap gap-1">
                            {egoGraph.external_deps.slice(0, 15).map((dep, i) => (
                              <span
                                key={i}
                                className="px-2 py-0.5 bg-muted rounded text-xs"
                              >
                                {dep}
                              </span>
                            ))}
                            {egoGraph.external_deps.length > 15 && (
                              <span className="px-2 py-0.5 text-xs text-muted-foreground">
                                +{egoGraph.external_deps.length - 15} more
                              </span>
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    Failed to load file dependencies
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {!selectedFile && (
            <Card className="border-dashed">
              <CardContent className="py-12 text-center">
                <Search className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">
                  Search for a file above or click on any file in the lists to see its dependencies
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
