'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Download, Copy, Check, ZoomIn, ZoomOut, RefreshCw, AlertCircle, Loader2, ArrowRight, ArrowDown, FolderTree, Home } from 'lucide-react';
import mermaid from 'mermaid';
import DOMPurify from 'dompurify';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAppStore } from '@/lib/store';
import { api } from '@/lib/api';
import { DependencyOverview } from '@/components/dependencies';
import { AnalysisInProgress } from '@/components/ui/loading-skeleton';
import type { Diagram } from '@/types/api';

// Initialize mermaid with settings for directory diagrams
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
  maxTextSize: 100000,
  themeVariables: {
    fontSize: '16px',
    fontFamily: 'ui-sans-serif, system-ui, sans-serif',
  },
  flowchart: {
    useMaxWidth: false,  // Render at natural size for consistent sizing between LR/TD
    htmlLabels: true,
    curve: 'basis',
    nodeSpacing: 30,
    rankSpacing: 50,
    padding: 15,
  },
});

interface MermaidDiagramProps {
  chart: string;
  id: string;
}

function MermaidDiagram({ chart, id }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [copied, setCopied] = useState(false);

  // Pan/drag state
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [scrollStart, setScrollStart] = useState({ x: 0, y: 0 });

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current) return;
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
    setScrollStart({
      x: containerRef.current.scrollLeft,
      y: containerRef.current.scrollTop,
    });
    e.preventDefault();
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !containerRef.current) return;
    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;
    containerRef.current.scrollLeft = scrollStart.x - deltaX;
    containerRef.current.scrollTop = scrollStart.y - deltaY;
  }, [isDragging, dragStart, scrollStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!chart) return;
      try {
        const uniqueId = `mermaid-${id}-${Date.now()}`;
        const { svg } = await mermaid.render(uniqueId, chart);
        // Sanitize the SVG output with DOMPurify to prevent XSS
        const sanitizedSvg = DOMPurify.sanitize(svg, {
          USE_PROFILES: { svg: true, svgFilters: true },
          ADD_TAGS: ['foreignObject'],
        });
        setSvg(sanitizedSvg);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : String(err);
        setError(`Failed to render diagram: ${errorMessage}`);
      }
    };
    renderDiagram();
  }, [chart, id]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${id}-diagram.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-full min-h-[200px] text-muted-foreground bg-muted/30 rounded-lg p-4">
        {error}
      </div>
    );
  }

  // SVG content is sanitized with DOMPurify above before being stored
  return (
    <div className="relative h-full flex flex-col">
      <div className="absolute top-2 right-2 z-10 flex items-center gap-1">
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.max(0.25, z - 0.25))}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <span className="text-xs text-muted-foreground w-12 text-center">{Math.round(zoom * 100)}%</span>
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.min(4, z + 0.25))}>
          <ZoomIn className="h-4 w-4" />
        </Button>
        <div className="w-px h-6 bg-border mx-1" />
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleCopy}>
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleDownload} disabled={!svg}>
          <Download className="h-4 w-4" />
        </Button>
      </div>

      <div
        ref={containerRef}
        className={`overflow-auto p-4 bg-muted/30 rounded-lg flex-1 min-h-[200px] ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {svg ? (
          <div
            className="inline-block origin-top-left select-none"
            style={{ transform: `scale(${zoom})` }}
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        ) : (
          <div className="h-full flex items-center justify-center animate-pulse text-muted-foreground">
            Loading diagram...
          </div>
        )}
      </div>
    </div>
  );
}

type TabType = 'dependencies' | 'directory';

export function DiagramsTab() {
  const { currentProjectId, projects } = useAppStore();
  const [activeTab, setActiveTab] = useState<TabType>('dependencies');

  // Directory diagram state
  const [directoryDiagram, setDirectoryDiagram] = useState<Diagram | null>(null);
  const [directoryLoading, setDirectoryLoading] = useState(false);
  const [directoryError, setDirectoryError] = useState<string | null>(null);
  const [diagramDirection, setDiagramDirection] = useState<'LR' | 'TD'>('LR');
  const [currentPath, setCurrentPath] = useState<string>('');
  const [availablePaths, setAvailablePaths] = useState<string[]>([]);

  const currentProject = projects.find(p => p.id === currentProjectId);
  const isProjectReady = currentProject?.status === 'ready';

  // Fetch directory diagram
  const fetchDirectoryDiagram = useCallback(async (
    direction: 'LR' | 'TD' = diagramDirection,
    path: string = currentPath
  ) => {
    if (!currentProjectId || !isProjectReady) return;

    setDirectoryLoading(true);
    setDirectoryError(null);

    try {
      const diagram = await api.getDiagram(currentProjectId, 'directory', { direction, path });
      setDirectoryDiagram(diagram);
      // Extract available paths from metadata for navigation
      if (diagram.metadata?.available_paths) {
        setAvailablePaths(diagram.metadata.available_paths as string[]);
      }
    } catch (err: any) {
      setDirectoryError(err?.message || 'Failed to load directory diagram');
    } finally {
      setDirectoryLoading(false);
    }
  }, [currentProjectId, isProjectReady, diagramDirection, currentPath]);

  // Toggle diagram direction
  const toggleDirection = useCallback(() => {
    const newDirection = diagramDirection === 'LR' ? 'TD' : 'LR';
    setDiagramDirection(newDirection);
    fetchDirectoryDiagram(newDirection, currentPath);
  }, [diagramDirection, currentPath, fetchDirectoryDiagram]);

  // Navigate to a subdirectory
  const navigateToPath = useCallback((path: string) => {
    setCurrentPath(path);
    fetchDirectoryDiagram(diagramDirection, path);
  }, [diagramDirection, fetchDirectoryDiagram]);

  // Load directory diagram when tab is selected
  useEffect(() => {
    if (activeTab === 'directory' && !directoryDiagram && !directoryLoading && !directoryError) {
      fetchDirectoryDiagram();
    }
  }, [activeTab, directoryDiagram, directoryLoading, directoryError, fetchDirectoryDiagram]);

  // Reset when project changes
  useEffect(() => {
    setDirectoryDiagram(null);
    setDirectoryError(null);
    setCurrentPath('');
    setAvailablePaths([]);
  }, [currentProjectId]);

  if (!currentProject) {
    return (
      <div className="p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>No Project Selected</AlertTitle>
          <AlertDescription>
            Please select a project to view its diagrams.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Check if analysis is in progress (must match backend ProjectStatus enum)
  const analysisStates = ['pending', 'cloning', 'scanning', 'analyzing', 'embedding'];
  const isAnalyzing = analysisStates.includes(currentProject.status);

  if (!isProjectReady) {
    // Show loading state while analyzing, otherwise show "Analysis Required"
    if (isAnalyzing) {
      return (
        <div className="p-6">
          <AnalysisInProgress status={currentProject.status} />
        </div>
      );
    }
    return (
      <div className="p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Analysis Required</AlertTitle>
          <AlertDescription>
            Please run analysis on this project first to generate diagrams.
            Current status: {currentProject.status}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-4 h-full flex flex-col overflow-hidden">
      <div className="flex-1 min-h-0 flex flex-col">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabType)} className="flex-1 flex flex-col min-h-0">
          <TabsList className="flex-shrink-0 w-fit">
            <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
            <TabsTrigger value="directory">Directory Structure</TabsTrigger>
          </TabsList>

          <TabsContent value="dependencies" className="flex-1 min-h-0 mt-2 overflow-auto">
            <DependencyOverview projectId={currentProjectId!} />
          </TabsContent>

          <TabsContent value="directory" className="flex-1 min-h-0 mt-2">
            <Card className="h-full flex flex-col">
              <CardHeader className="flex flex-row items-center justify-between flex-shrink-0 py-2 px-4">
                <div>
                  <CardTitle className="text-base">Directory Structure</CardTitle>
                  <CardDescription className="text-xs">
                    File system organization and folder hierarchy
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {/* Navigation dropdown */}
                  {availablePaths.length > 0 && (
                    <div className="flex items-center gap-1">
                      {currentPath && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigateToPath('')}
                          disabled={directoryLoading}
                          title="Back to root"
                        >
                          <Home className="h-4 w-4" />
                        </Button>
                      )}
                      <select
                        className="h-8 px-2 text-sm border rounded-md bg-background"
                        value={currentPath}
                        onChange={(e) => navigateToPath(e.target.value)}
                        disabled={directoryLoading}
                      >
                        <option value="">Root (all)</option>
                        {availablePaths.map((path) => (
                          <option key={path} value={path}>
                            {path}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <div className="w-px h-6 bg-border" />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={toggleDirection}
                    disabled={directoryLoading}
                    title={diagramDirection === 'LR' ? 'Switch to top-down layout' : 'Switch to left-right layout'}
                  >
                    {diagramDirection === 'LR' ? (
                      <ArrowRight className="h-4 w-4" />
                    ) : (
                      <ArrowDown className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fetchDirectoryDiagram()}
                    disabled={directoryLoading}
                  >
                    {directoryLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="p-2 flex-1 min-h-0 flex flex-col">
                {directoryLoading ? (
                  <div className="flex items-center justify-center flex-1 min-h-[200px] bg-muted/30 rounded-lg">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    <span className="ml-2 text-muted-foreground">Generating diagram...</span>
                  </div>
                ) : directoryError ? (
                  <div className="flex-1 min-h-[200px] flex items-center justify-center">
                    <Alert variant="destructive" className="max-w-lg">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Error</AlertTitle>
                      <AlertDescription>{directoryError}</AlertDescription>
                    </Alert>
                  </div>
                ) : directoryDiagram ? (
                  <MermaidDiagram chart={directoryDiagram.mermaid_code} id="directory" />
                ) : (
                  <div className="flex items-center justify-center flex-1 min-h-[200px] bg-muted/30 rounded-lg text-muted-foreground">
                    <Button onClick={() => fetchDirectoryDiagram()}>
                      Generate Diagram
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
