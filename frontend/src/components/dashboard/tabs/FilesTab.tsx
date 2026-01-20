'use client';

import { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { mockFileTree, mockFileContent } from '@/lib/mock-data';
import { MockDataIndicator } from '@/components/ui/mock-data-indicator';
import { AnalysisInProgress } from '@/components/ui/loading-skeleton';
import { useAppStore } from '@/lib/store';

interface FileNode {
  name: string;
  type: 'file' | 'directory';
  language?: string;
  lines?: number;
  children?: FileNode[];
}

interface TreeNodeProps {
  node: FileNode;
  depth: number;
  onSelect: (node: FileNode) => void;
  selectedFile: string | null;
}

function TreeNode({ node, depth, onSelect, selectedFile }: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(depth < 2);

  const isSelected = selectedFile === node.name;
  const hasChildren = node.type === 'directory' && node.children && node.children.length > 0;

  const getLanguageColor = (lang?: string) => {
    const colors: Record<string, string> = {
      python: 'bg-blue-500',
      javascript: 'bg-yellow-500',
      typescript: 'bg-blue-600',
      markdown: 'bg-gray-500',
      dockerfile: 'bg-cyan-500',
      text: 'bg-gray-400',
    };
    return colors[lang || ''] || 'bg-gray-400';
  };

  return (
    <div>
      <div
        className={`flex items-center gap-1 py-1 px-2 rounded cursor-pointer hover:bg-muted/50 ${
          isSelected ? 'bg-primary/10 text-primary' : ''
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => {
          if (hasChildren) {
            setIsExpanded(!isExpanded);
          } else {
            onSelect(node);
          }
        }}
      >
        {/* Expand/collapse icon */}
        {hasChildren ? (
          isExpanded ? (
            <ChevronDown className="h-4 w-4 flex-shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 flex-shrink-0" />
          )
        ) : (
          <span className="w-4" />
        )}

        {/* File/folder icon */}
        {node.type === 'directory' ? (
          isExpanded ? (
            <FolderOpen className="h-4 w-4 text-yellow-500 flex-shrink-0" />
          ) : (
            <Folder className="h-4 w-4 text-yellow-500 flex-shrink-0" />
          )
        ) : (
          <File className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        )}

        {/* Name */}
        <span className="text-sm truncate flex-1">{node.name}</span>

        {/* File info */}
        {node.type === 'file' && node.language && (
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${getLanguageColor(node.language)}`} />
            {node.lines && (
              <span className="text-xs text-muted-foreground">{node.lines}L</span>
            )}
          </div>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child, index) => (
            <TreeNode
              key={`${child.name}-${index}`}
              node={child}
              depth={depth + 1}
              onSelect={onSelect}
              selectedFile={selectedFile}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function FilesTab() {
  const { currentProjectId, projects } = useAppStore();
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const currentProject = projects.find(p => p.id === currentProjectId);

  // Check if analysis is in progress (must match backend ProjectStatus enum)
  const analysisStates = ['pending', 'cloning', 'scanning', 'analyzing', 'embedding'];
  const isAnalyzing = currentProject && analysisStates.includes(currentProject.status);

  const handleFileSelect = (node: FileNode) => {
    if (node.type === 'file') {
      setSelectedFile(node);
    }
  };

  // Show loading state while analyzing
  if (isAnalyzing) {
    return (
      <div className="p-6">
        <AnalysisInProgress status={currentProject.status} />
      </div>
    );
  }

  return (
    <div className="p-6 h-full">
      <MockDataIndicator label="All Files Mock Data" variant="overlay">
      <div className="grid grid-cols-[350px_1fr] gap-6 h-[calc(100vh-12rem)]">
        {/* File Tree */}
        <Card className="flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">File Explorer</CardTitle>
            <div className="relative mt-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <ScrollArea className="h-full px-4 pb-4">
              <TreeNode
                node={mockFileTree as FileNode}
                depth={0}
                onSelect={handleFileSelect}
                selectedFile={selectedFile?.name || null}
              />
            </ScrollArea>
          </CardContent>
        </Card>

        {/* File Content */}
        <Card className="flex flex-col">
          {selectedFile ? (
            <>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-mono">{selectedFile.name}</CardTitle>
                    <CardDescription>
                      {selectedFile.language && (
                        <Badge variant="secondary" className="mt-1">
                          {selectedFile.language}
                        </Badge>
                      )}
                      {selectedFile.lines && (
                        <span className="ml-2 text-muted-foreground">
                          {selectedFile.lines} lines
                        </span>
                      )}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden p-0">
                <ScrollArea className="h-full">
                  <pre className="p-4 text-sm font-mono bg-muted/30 min-h-full">
                    <code>{mockFileContent}</code>
                  </pre>
                </ScrollArea>
              </CardContent>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center">
                <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a file to view its contents</p>
              </div>
            </div>
          )}
        </Card>
      </div>
      </MockDataIndicator>
    </div>
  );
}
