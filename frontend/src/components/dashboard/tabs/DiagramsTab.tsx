'use client';

import { useEffect, useRef, useState } from 'react';
import { Download, Copy, Check, ZoomIn, ZoomOut } from 'lucide-react';
import mermaid from 'mermaid';
import DOMPurify from 'dompurify';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { mockDiagrams } from '@/lib/mock-data';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
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
  const [zoom, setZoom] = useState(1);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!chart) return;

      try {
        const { svg } = await mermaid.render(`mermaid-${id}`, chart);
        // Sanitize the SVG output to prevent XSS
        const sanitizedSvg = DOMPurify.sanitize(svg, {
          USE_PROFILES: { svg: true, svgFilters: true },
          ADD_TAGS: ['foreignObject'],
        });
        setSvg(sanitizedSvg);
        setError(null);
      } catch (err) {
        setError('Failed to render diagram');
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
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        {error}
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Controls */}
      <div className="absolute top-2 right-2 z-10 flex items-center gap-1">
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <span className="text-xs text-muted-foreground w-12 text-center">{Math.round(zoom * 100)}%</span>
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setZoom(z => Math.min(2, z + 0.25))}>
          <ZoomIn className="h-4 w-4" />
        </Button>
        <div className="w-px h-6 bg-border mx-1" />
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleCopy}>
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
        <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleDownload}>
          <Download className="h-4 w-4" />
        </Button>
      </div>

      {/* Diagram */}
      <div
        ref={containerRef}
        className="overflow-auto p-4 bg-muted/30 rounded-lg min-h-[400px] flex items-center justify-center"
        style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
      >
        {svg ? (
          <div dangerouslySetInnerHTML={{ __html: svg }} />
        ) : (
          <div className="animate-pulse text-muted-foreground">Loading diagram...</div>
        )}
      </div>
    </div>
  );
}

export function DiagramsTab() {
  const [activeDiagram, setActiveDiagram] = useState<'architecture' | 'dependency' | 'directory'>('architecture');

  const diagrams = [
    {
      id: 'architecture',
      title: 'Architecture Diagram',
      description: 'High-level system architecture showing main components and their relationships',
      chart: mockDiagrams.architecture,
    },
    {
      id: 'dependency',
      title: 'Dependency Graph',
      description: 'Internal module dependencies and their connections',
      chart: mockDiagrams.dependency,
    },
    {
      id: 'directory',
      title: 'Directory Structure',
      description: 'File system organization and folder hierarchy',
      chart: mockDiagrams.directory,
    },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Architecture Diagrams</h1>
        <p className="text-muted-foreground mt-1">
          Visual representations of the codebase structure and dependencies
        </p>
      </div>

      <Tabs value={activeDiagram} onValueChange={(v) => setActiveDiagram(v as any)}>
        <TabsList>
          <TabsTrigger value="architecture">Architecture</TabsTrigger>
          <TabsTrigger value="dependency">Dependencies</TabsTrigger>
          <TabsTrigger value="directory">Directory</TabsTrigger>
        </TabsList>

        {diagrams.map((diagram) => (
          <TabsContent key={diagram.id} value={diagram.id}>
            <Card>
              <CardHeader>
                <CardTitle>{diagram.title}</CardTitle>
                <CardDescription>{diagram.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <MermaidDiagram chart={diagram.chart} id={diagram.id} />
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {/* Mermaid Source Code */}
      <Card>
        <CardHeader>
          <CardTitle>Mermaid Source</CardTitle>
          <CardDescription>
            Edit or copy this Mermaid code to customize the diagram
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm font-mono">
            {diagrams.find(d => d.id === activeDiagram)?.chart}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
