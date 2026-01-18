'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Download, Copy, Check, ZoomIn, ZoomOut, RefreshCw, AlertCircle, Loader2 } from 'lucide-react';
import mermaid from 'mermaid';
import DOMPurify from 'dompurify';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAppStore } from '@/lib/store';
import { api } from '@/lib/api';
import type { Diagram, DiagramType } from '@/types/api';

// Initialize mermaid with increased maxTextSize for large diagrams
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
  maxTextSize: 100000, // Increased from default 50000 to handle larger diagrams
  flowchart: {
    useMaxWidth: true,
    htmlLabels: true,
    curve: 'basis',
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
  const [zoom, setZoom] = useState(10);
  const [copied, setCopied] = useState(false);

  // Pan/drag state
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [scrollStart, setScrollStart] = useState({ x: 0, y: 0 });

  // Handle mouse down - start dragging
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current) return;
    // Only start drag on left mouse button
    if (e.button !== 0) return;

    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
    setScrollStart({
      x: containerRef.current.scrollLeft,
      y: containerRef.current.scrollTop,
    });
    e.preventDefault();
  }, []);

  // Handle mouse move - drag to pan
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !containerRef.current) return;

    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;

    containerRef.current.scrollLeft = scrollStart.x - deltaX;
    containerRef.current.scrollTop = scrollStart.y - deltaY;
  }, [isDragging, dragStart, scrollStart]);

  // Handle mouse up - stop dragging
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Handle mouse leave - stop dragging if mouse leaves container
  const handleMouseLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!chart) return;

      try {
        // Generate unique ID for this render to avoid conflicts
        const uniqueId = `mermaid-${id}-${Date.now()}`;
        const { svg } = await mermaid.render(uniqueId, chart);
        // Sanitize the SVG output to prevent XSS
        const sanitizedSvg = DOMPurify.sanitize(svg, {
          USE_PROFILES: { svg: true, svgFilters: true },
          ADD_TAGS: ['foreignObject'],
        });
        setSvg(sanitizedSvg);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : String(err);
        if (errorMessage.includes('Maximum text size') || errorMessage.includes('maxTextSize')) {
          setError(`Diagram too large to render (${chart.length.toLocaleString()} characters). Try the "Directory" diagram which is typically smaller.`);
        } else {
          setError(`Failed to render diagram: ${errorMessage}`);
        }
        console.error('Mermaid error:', err);
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

  return (
    <div className="relative h-full flex flex-col">
      {/* Controls */}
      <div className="absolute top-2 right-2 z-10 flex items-center gap-1">
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.max(0.25, z - 0.50))}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <span className="text-xs text-muted-foreground w-16 text-center">{Math.round(zoom * 100)}%</span>
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.min(20, z + 0.50))}>
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

      {/* Diagram - fills available height, SVG is sanitized with DOMPurify before being stored */}
      <div
        ref={containerRef}
        className={`overflow-auto p-4 bg-muted/30 rounded-lg flex-1 min-h-[200px] ${
          isDragging ? 'cursor-grabbing' : 'cursor-grab'
        }`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      >
        {svg ? (
          <div
            className="inline-block origin-top-left select-none"
            style={{ transform: `scale(${zoom})` }}
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        ) : (
          <div className="h-full flex items-center justify-center animate-pulse text-muted-foreground">Loading diagram...</div>
        )}
      </div>
    </div>
  );
}

interface DiagramData {
  type: DiagramType;
  title: string;
  description: string;
  diagram: Diagram | null;
  loading: boolean;
  error: string | null;
}

/**
 * Extract only displayable statistics from diagram metadata.
 * Filters out complex objects (nodes, edges, groups, colors) and shows
 * clean summary numbers instead.
 */
function getDisplayableStats(metadata: Record<string, unknown>): Record<string, string | number> {
  const displayable: Record<string, string | number> = {};

  // Extract from stats sub-object if present
  const stats = metadata.stats as Record<string, unknown> | undefined;
  if (stats) {
    if (typeof stats.total_nodes === 'number') displayable['Total Nodes'] = stats.total_nodes;
    if (typeof stats.total_edges === 'number') displayable['Total Edges'] = stats.total_edges;
    if (typeof stats.max_depth === 'number') displayable['Max Depth'] = stats.max_depth;
  }

  // Count items in complex objects instead of showing raw data
  if (metadata.nodes && typeof metadata.nodes === 'object' && !Array.isArray(metadata.nodes)) {
    const nodeCount = Object.keys(metadata.nodes as object).length;
    if (!displayable['Total Nodes']) displayable['Node Count'] = nodeCount;
  }
  if (Array.isArray(metadata.edges)) {
    const edgeCount = metadata.edges.length;
    if (!displayable['Total Edges']) displayable['Edge Count'] = edgeCount;
  }
  if (metadata.groups && typeof metadata.groups === 'object') {
    displayable['Group Count'] = Object.keys(metadata.groups as object).length;
  }
  if (metadata.colors && typeof metadata.colors === 'object') {
    displayable['Languages'] = Object.keys(metadata.colors as object).length;
  }

  // Include simple scalar values directly (excluding known complex keys)
  const excludeKeys = new Set(['nodes', 'edges', 'groups', 'colors', 'stats']);
  for (const [key, value] of Object.entries(metadata)) {
    if (excludeKeys.has(key)) continue;
    if (typeof value === 'string' || typeof value === 'number') {
      displayable[key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())] = value;
    }
  }

  return displayable;
}

export function DiagramsTab() {
  const { currentProjectId, projects } = useAppStore();
  const [activeDiagram, setActiveDiagram] = useState<DiagramType>('dependency');
  const [diagrams, setDiagrams] = useState<Record<DiagramType, DiagramData>>({
    dependency: {
      type: 'dependency',
      title: 'Dependency Graph',
      description: 'Internal module dependencies and their connections',
      diagram: null,
      loading: false,
      error: null,
    },
    directory: {
      type: 'directory',
      title: 'Directory Structure',
      description: 'File system organization and folder hierarchy',
      diagram: null,
      loading: false,
      error: null,
    },
    architecture: {
      type: 'architecture',
      title: 'Architecture Diagram',
      description: 'High-level system architecture showing main components',
      diagram: null,
      loading: false,
      error: null,
    },
    class: {
      type: 'class',
      title: 'Class Diagram',
      description: 'Class hierarchies and relationships',
      diagram: null,
      loading: false,
      error: null,
    },
    sequence: {
      type: 'sequence',
      title: 'Sequence Diagram',
      description: 'Request flow and component interactions',
      diagram: null,
      loading: false,
      error: null,
    },
  });
  const [regenerating, setRegenerating] = useState(false);

  // Get current project
  const currentProject = projects.find(p => p.id === currentProjectId);
  const isProjectReady = currentProject?.status === 'ready';

  // Fetch a specific diagram
  const fetchDiagram = useCallback(async (type: DiagramType) => {
    if (!currentProjectId || !isProjectReady) return;

    setDiagrams(prev => ({
      ...prev,
      [type]: { ...prev[type], loading: true, error: null },
    }));

    try {
      const diagram = await api.getDiagram(currentProjectId, type);
      setDiagrams(prev => ({
        ...prev,
        [type]: { ...prev[type], diagram, loading: false },
      }));
    } catch (err: any) {
      const errorMessage = err?.status === 501
        ? 'This diagram type is not yet implemented'
        : err?.message || 'Failed to load diagram';

      setDiagrams(prev => ({
        ...prev,
        [type]: { ...prev[type], loading: false, error: errorMessage },
      }));
    }
  }, [currentProjectId, isProjectReady]);

  // Fetch diagram when tab changes or project changes
  useEffect(() => {
    const currentDiagram = diagrams[activeDiagram];
    // Don't fetch if we already have the diagram, are currently loading, or had an error
    if (currentProjectId && isProjectReady && !currentDiagram.diagram && !currentDiagram.loading && !currentDiagram.error) {
      fetchDiagram(activeDiagram);
    }
  }, [activeDiagram, currentProjectId, isProjectReady, fetchDiagram, diagrams]);

  // Regenerate all diagrams
  const handleRegenerateAll = async () => {
    if (!currentProjectId) return;

    setRegenerating(true);
    try {
      // Call the regenerate endpoint
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${currentProjectId}/diagrams/generate`, {
        method: 'POST',
      });

      // Refetch current diagram
      await fetchDiagram(activeDiagram);
    } catch (err) {
      console.error('Failed to regenerate diagrams:', err);
    } finally {
      setRegenerating(false);
    }
  };

  // Available diagram types (only show implemented ones prominently)
  const availableDiagrams: DiagramType[] = ['dependency', 'directory'];
  const comingSoonDiagrams: DiagramType[] = ['architecture', 'class', 'sequence'];

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

  if (!isProjectReady) {
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

  const currentDiagramData = diagrams[activeDiagram];

  // Check if we have displayable statistics
  const hasStatistics = currentDiagramData.diagram?.metadata &&
    Object.keys(getDisplayableStats(currentDiagramData.diagram.metadata as Record<string, unknown>)).length > 0;

  return (
    <div className="p-4 h-full flex flex-col overflow-hidden">
      {/* Header - fixed height */}
      <div className="flex items-center justify-between flex-shrink-0 mb-2">
        <div>
          <h1 className="text-xl font-bold">Architecture Diagrams</h1>
          <p className="text-muted-foreground text-sm">
            Visual representations of the codebase structure and dependencies
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleRegenerateAll}
          disabled={regenerating}
        >
          {regenerating ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Regenerate All
        </Button>
      </div>

      {/* Diagram area - fills remaining space */}
      <div className="flex-1 min-h-0 flex flex-col">
        <Tabs value={activeDiagram} onValueChange={(v) => setActiveDiagram(v as DiagramType)} className="flex-1 flex flex-col min-h-0">
          <TabsList className="flex-shrink-0">
            {availableDiagrams.map((type) => (
              <TabsTrigger key={type} value={type}>
                {diagrams[type].title.replace(' Diagram', '').replace(' Graph', '')}
              </TabsTrigger>
            ))}
            {comingSoonDiagrams.map((type) => (
              <TabsTrigger key={type} value={type} disabled className="opacity-50">
                {diagrams[type].title.replace(' Diagram', '')}
                <span className="ml-1 text-xs">(Soon)</span>
              </TabsTrigger>
            ))}
          </TabsList>

          {Object.entries(diagrams).map(([type, data]) => (
            <TabsContent key={type} value={type} className="flex-1 min-h-0 mt-1">
              <Card className="h-full flex flex-col">
                <CardHeader className="flex flex-row items-center justify-between flex-shrink-0 py-2 px-4">
                  <div>
                    <CardTitle className="text-base">{data.title}</CardTitle>
                    <CardDescription className="text-xs">{data.description}</CardDescription>
                  </div>
                  {data.diagram && (
                    <div className="text-xs text-muted-foreground">
                      Generated: {new Date(data.diagram.generated_at).toLocaleString()}
                    </div>
                  )}
                </CardHeader>
                <CardContent className="p-2 flex-1 min-h-0 flex flex-col">
                  {data.loading ? (
                    <div className="flex items-center justify-center flex-1 min-h-[200px] bg-muted/30 rounded-lg">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                      <span className="ml-2 text-muted-foreground">Generating diagram...</span>
                    </div>
                  ) : data.error ? (
                    <div className="flex-1 min-h-[200px] flex items-center justify-center">
                      <Alert variant="destructive" className="max-w-lg">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>{data.error}</AlertDescription>
                      </Alert>
                    </div>
                  ) : data.diagram ? (
                    <MermaidDiagram chart={data.diagram.mermaid_code} id={type} />
                  ) : (
                    <div className="flex items-center justify-center flex-1 min-h-[200px] bg-muted/30 rounded-lg text-muted-foreground">
                      <Button onClick={() => fetchDiagram(type as DiagramType)}>
                        Generate Diagram
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      </div>

      {/* Diagram Statistics - fixed at bottom */}
      {hasStatistics && (
        <Card className="flex-shrink-0 mt-2">
          <CardContent className="py-2 px-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-muted-foreground">Statistics:</span>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2 text-sm">
              {Object.entries(getDisplayableStats(currentDiagramData.diagram!.metadata as Record<string, unknown>)).map(([key, value]) => (
                <div key={key} className="flex flex-col px-2 py-1 bg-muted/50 rounded">
                  <span className="text-muted-foreground text-xs truncate">{key}</span>
                  <span className="font-semibold">
                    {typeof value === 'number' ? value.toLocaleString() : value}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
