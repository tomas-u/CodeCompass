'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, X, Bot, User, Copy, Check, FileCode, Minimize2, Maximize2, Trash2, Plus, History } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { useAppStore, ChatMessage } from '@/lib/store';
import { api } from '@/lib/api';

export function ChatPanel() {
  const {
    toggleChatPanel,
    chatMessages,
    addChatMessage,
    updateChatMessage,
    isAiTyping,
    setIsAiTyping,
    clearChat,
    currentProjectId,
    currentSessionId,
    setCurrentSessionId,
    chatSessions,
    setChatSessions,
    isLoadingSessions,
    setIsLoadingSessions,
    setChatMessages,
  } = useAppStore();

  const [inputValue, setInputValue] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollThrottleRef = useRef<number | null>(null);
  const lastMessageCountRef = useRef<number>(0);
  const loadedProjectRef = useRef<string | null>(null);

  // Track when component is mounted (client-side only)
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Load session when project changes
  useEffect(() => {
    if (!currentProjectId || loadedProjectRef.current === currentProjectId) {
      return;
    }

    loadedProjectRef.current = currentProjectId;
    loadOrCreateSession();
  }, [currentProjectId]);

  // Load or create a session for the current project
  const loadOrCreateSession = async () => {
    if (!currentProjectId) return;

    setIsLoadingSessions(true);
    setSessionError(null);

    try {
      // First, try to list existing sessions
      const sessions = await api.listChatSessions(currentProjectId);
      setChatSessions(sessions);

      if (sessions.length > 0) {
        // Load the most recent session
        const latestSession = sessions[0]; // Sessions are sorted by updated_at desc
        await loadSession(latestSession.id);
      } else {
        // Create a new session - this will include the AI intro
        await createNewSession();
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setSessionError('Failed to load chat sessions');
    } finally {
      setIsLoadingSessions(false);
    }
  };

  // Load a specific session
  const loadSession = async (sessionId: string) => {
    if (!currentProjectId) return;

    try {
      const session = await api.getChatSession(currentProjectId, sessionId);
      setCurrentSessionId(session.id);

      // Convert API messages to store format
      const messages: ChatMessage[] = session.messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        sources: msg.sources?.map((s) => ({
          filePath: s.file_path,
          startLine: s.start_line,
          endLine: s.end_line,
          snippet: s.snippet,
        })),
        createdAt: msg.created_at,
      }));

      setChatMessages(messages);
    } catch (error) {
      console.error('Failed to load session:', error);
      setSessionError('Failed to load chat session');
    }
  };

  // Create a new session
  const createNewSession = async () => {
    if (!currentProjectId) return;

    try {
      const session = await api.createChatSession(currentProjectId);
      setCurrentSessionId(session.id);

      // Convert API messages to store format (includes intro message)
      const messages: ChatMessage[] = session.messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        sources: msg.sources?.map((s) => ({
          filePath: s.file_path,
          startLine: s.start_line,
          endLine: s.end_line,
          snippet: s.snippet,
        })),
        createdAt: msg.created_at,
      }));

      setChatMessages(messages);

      // Refresh sessions list
      const sessions = await api.listChatSessions(currentProjectId);
      setChatSessions(sessions);
    } catch (error) {
      console.error('Failed to create session:', error);
      setSessionError('Failed to create chat session');
    }
  };

  // Handle starting a new conversation
  const handleNewConversation = async () => {
    await createNewSession();
  };

  // Handle switching to a different session
  const handleSwitchSession = async (sessionId: string) => {
    await loadSession(sessionId);
  };

  // Throttled scroll function for smooth streaming
  const scrollToBottom = useCallback((smooth: boolean = false) => {
    if (scrollThrottleRef.current) return; // Already scheduled

    scrollThrottleRef.current = requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({
        behavior: smooth ? 'smooth' : 'instant',
        block: 'end'
      });
      scrollThrottleRef.current = null;
    });
  }, []);

  // Get last message content length to trigger scroll during streaming
  const lastMessageContent = chatMessages[chatMessages.length - 1]?.content || '';

  // Auto-scroll to bottom when messages change or content streams in
  useEffect(() => {
    const isNewMessage = chatMessages.length !== lastMessageCountRef.current;
    lastMessageCountRef.current = chatMessages.length;

    // Use smooth scroll for new messages, instant for streaming updates
    scrollToBottom(isNewMessage && !isAiTyping);
  }, [chatMessages.length, lastMessageContent, isAiTyping, scrollToBottom]);

  // Cleanup throttle on unmount
  useEffect(() => {
    return () => {
      if (scrollThrottleRef.current) {
        cancelAnimationFrame(scrollThrottleRef.current);
      }
    };
  }, []);

  // Keyboard shortcut: Cmd+K (Mac) or Ctrl+K (Windows/Linux) to focus chat
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (!useAppStore.getState().isChatPanelOpen) {
          toggleChatPanel();
        }
        // Small delay to ensure panel is open before focusing
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleChatPanel]);

  const handleSend = async () => {
    if (!inputValue.trim() || !currentProjectId) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      createdAt: new Date().toISOString(),
    };

    addChatMessage(userMessage);
    const messageContent = inputValue.trim();
    setInputValue('');
    setIsAiTyping(true);

    // Buffer sources and message ID until first token arrives
    let pendingSources: { filePath: string; startLine: number; endLine: number; snippet: string; }[] = [];
    let aiMessageId: string | null = null;

    try {
      await api.sendChatMessageStreaming(
        currentProjectId,
        messageContent,
        // onToken - append token to message content
        (token) => {
          // On first token, create the message with sources
          if (!aiMessageId) {
            aiMessageId = (Date.now() + 1).toString();
            const aiMessage: ChatMessage = {
              id: aiMessageId,
              role: 'assistant',
              content: token,
              createdAt: new Date().toISOString(),
              sources: pendingSources,
            };
            addChatMessage(aiMessage);
          } else {
            updateChatMessage(aiMessageId, (msg) => ({
              ...msg,
              content: msg.content + token,
            }));
          }
        },
        // onSources - buffer sources until first token
        (sources) => {
          pendingSources = sources.map(s => ({
            filePath: s.file_path,
            startLine: s.start_line,
            endLine: s.end_line,
            snippet: s.snippet,
          }));
        },
        // onDone
        () => {
          setIsAiTyping(false);
        },
        // onError
        (error) => {
          // If we already started a message, append error to it
          if (aiMessageId) {
            updateChatMessage(aiMessageId, (msg) => ({
              ...msg,
              content: msg.content
                ? msg.content + `\n\n**Error:** ${error.message}`
                : `**Error:** ${error.message}`,
            }));
          } else {
            // Create error message if no tokens were received
            const errorMessageId = (Date.now() + 1).toString();
            addChatMessage({
              id: errorMessageId,
              role: 'assistant',
              content: `**Error:** ${error.message}`,
              createdAt: new Date().toISOString(),
            });
          }
          setIsAiTyping(false);
        },
        // sessionId - pass current session for message threading
        currentSessionId,
        // onSession - update session ID when backend creates/returns one
        (sessionId) => {
          setCurrentSessionId(sessionId);
        },
      );
    } catch (error) {
      console.error('Chat streaming error:', error);
      // Create error message if streaming failed entirely
      if (!aiMessageId) {
        const errorMessageId = (Date.now() + 1).toString();
        addChatMessage({
          id: errorMessageId,
          role: 'assistant',
          content: `**Error:** Unable to get a response from the AI. Please check that the backend services are running.\n\n${error instanceof Error ? error.message : 'Unknown error'}`,
          createdAt: new Date().toISOString(),
        });
      }
      setIsAiTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatTimestamp = (isoString: string) => {
    // Return empty string on server to avoid hydration mismatch
    if (!isMounted) return '';

    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    // For older messages, show time
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessageContent = (content: string) => {
    // Split by code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);

    return parts.map((part, index) => {
      if (part.startsWith('```')) {
        const match = part.match(/```(\w+)?\n?([\s\S]*?)```/);
        if (match) {
          const language = match[1] || 'text';
          const code = match[2].trim();
          return (
            <div key={index} className="relative my-3 rounded-lg overflow-hidden border border-border">
              <div className="flex items-center justify-between px-4 py-2 bg-muted/80 border-b border-border">
                <span className="text-xs font-mono text-muted-foreground uppercase">{language}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2"
                  onClick={() => copyToClipboard(code, `${index}`)}
                >
                  {copiedId === `${index}` ? (
                    <Check className="h-3 w-3" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              </div>
              <SyntaxHighlighter
                language={language}
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  padding: '1rem',
                  fontSize: '0.875rem',
                  background: 'hsl(var(--muted))',
                }}
                codeTagProps={{
                  style: {
                    fontFamily: 'var(--font-mono, monospace)',
                  }
                }}
              >
                {code}
              </SyntaxHighlighter>
            </div>
          );
        }
      }

      // Handle inline code and bold text
      const inlineParts = part.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
      return (
        <span key={index}>
          {inlineParts.map((inlinePart, i) => {
            if (inlinePart.startsWith('`') && inlinePart.endsWith('`')) {
              return (
                <code key={i} className="px-1.5 py-0.5 rounded bg-muted text-sm font-mono">
                  {inlinePart.slice(1, -1)}
                </code>
              );
            }
            if (inlinePart.startsWith('**') && inlinePart.endsWith('**')) {
              return (
                <strong key={i}>{inlinePart.slice(2, -2)}</strong>
              );
            }
            return <span key={i}>{inlinePart}</span>;
          })}
        </span>
      );
    });
  };

  // Format session title for dropdown
  const formatSessionTitle = (title: string | undefined, createdAt: string) => {
    if (title) return title;
    const date = new Date(createdAt);
    return `Chat ${date.toLocaleDateString()}`;
  };

  return (
    <div className="w-full h-full border-l border-border bg-background flex flex-col">
      {/* Header */}
      <div className="border-b border-border bg-muted/30 px-4">
        <div className="flex items-center justify-between h-12">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <span className="font-medium">Ask about this codebase</span>
        </div>
        <div className="flex items-center gap-1">
          {/* Session selector dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                title="Chat history"
                data-testid="chat-history-button"
              >
                <History className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[250px]">
              <DropdownMenuLabel>Conversations</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleNewConversation}
                className="cursor-pointer"
              >
                <Plus className="h-4 w-4 mr-2" />
                New Conversation
              </DropdownMenuItem>
              {chatSessions.length > 0 && <DropdownMenuSeparator />}
              {chatSessions.map((session) => (
                <DropdownMenuItem
                  key={session.id}
                  onClick={() => handleSwitchSession(session.id)}
                  className={`cursor-pointer ${session.id === currentSessionId ? 'bg-accent' : ''}`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium truncate max-w-[200px]">
                      {formatSessionTitle(session.title, session.created_at)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {session.message_count} messages
                    </span>
                  </div>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleNewConversation}
            title="New conversation"
            data-testid="chat-new-button"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Maximize" : "Minimize"}
          >
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleChatPanel}
            title="Close"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        </div>
      </div>

      {/* Messages - Always rendered for proper flex layout */}
      <div className={`flex-1 overflow-hidden ${isMinimized ? 'hidden' : ''}`}>
        {/* Loading state */}
        {isLoadingSessions && (
          <div className="flex items-center justify-center h-full">
            <div className="text-muted-foreground">Loading chat...</div>
          </div>
        )}

        {/* Error state */}
        {sessionError && !isLoadingSessions && (
          <div className="p-4">
            <div className="text-destructive text-sm">{sessionError}</div>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={loadOrCreateSession}
            >
              Retry
            </Button>
          </div>
        )}

        {/* Messages */}
        {!isLoadingSessions && !sessionError && (
          <ScrollArea className="h-full p-4" ref={scrollRef}>
            <div className="space-y-4">
            {chatMessages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                data-testid={`chat-message-${message.role}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                )}
                <div
                  className={`max-w-[90%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">
                    {message.role === 'assistant'
                      ? renderMessageContent(message.content)
                      : message.content
                    }
                  </div>
                  <div className="text-xs opacity-70 mt-2">
                    {formatTimestamp(message.createdAt)}
                  </div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border/50">
                      <span className="text-xs text-muted-foreground">Sources:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {message.sources.map((source, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="text-xs cursor-pointer hover:bg-accent"
                          >
                            <FileCode className="h-3 w-3 mr-1" />
                            {source.filePath.split('/').pop()}:{source.startLine}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator */}
            {isAiTyping && (
              <div className="flex gap-3" data-testid="chat-typing-indicator">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="bg-muted rounded-lg px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            {/* Empty state when no messages */}
            {chatMessages.length === 0 && !isAiTyping && (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <Bot className="h-12 w-12 text-muted-foreground/30 mb-4" />
                <p className="text-muted-foreground text-sm">
                  Start a conversation about this codebase
                </p>
              </div>
            )}

            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        )}
      </div>

      {/* Input - Always at bottom */}
      <div className={`p-4 border-t border-border ${isMinimized ? 'hidden' : ''}`}>
        <div className="flex gap-2 items-end">
          <Textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the codebase... (⌘K)"
            className="flex-1 min-h-[44px] max-h-[120px] resize-none"
            rows={2}
            maxLength={500}
            data-testid="chat-input"
            disabled={isLoadingSessions || !!sessionError}
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim() || isAiTyping || isLoadingSessions || !!sessionError}
            className="h-[44px]"
            data-testid="chat-send-button"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
