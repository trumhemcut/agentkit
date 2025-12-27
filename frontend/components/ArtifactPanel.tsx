"use client";

import { useMemo } from 'react';
import { Message, isArtifactMessage } from '@/types/chat';
import { CodeRenderer } from './Canvas/CodeRenderer';
import { TextRenderer } from './Canvas/TextRenderer';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Copy, Download, FileCode, FileText, X } from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';
import { useCanvas } from '@/contexts/CanvasContext';

interface ArtifactPanelProps {
  message: Message;
  onClose?: () => void;
}

/**
 * ArtifactPanel component
 * Displays artifact messages (code or text) in a dedicated panel
 */
export function ArtifactPanel({ message, onClose }: ArtifactPanelProps) {
  const { 
    artifact, 
    isPartialUpdateActive, 
    partialUpdateBuffer, 
    partialUpdateSelection,
    setSelectedTextForChat
  } = useCanvas();

  if (!isArtifactMessage(message)) {
    console.warn('ArtifactPanel received non-artifact message');
    return null;
  }

  // Selection change handler
  const handleSelectionChange = (selection: any) => {
    console.log('[ArtifactPanel] Selection changed:', selection);
    if (selection && setSelectedTextForChat) {
      setSelectedTextForChat(selection);
    }
  };

  // Use artifact from context if available, otherwise use message content
  const displayContent = useMemo(() => {
    // If partial update is active, show the preview of the update
    // BUT only if we have actual content in the buffer to avoid clearing selection
    if (isPartialUpdateActive && partialUpdateSelection && artifact && partialUpdateBuffer.length > 0) {
      const { start, end } = partialUpdateSelection;
      console.log('[ArtifactPanel] Preview update:', {
        start, 
        end, 
        bufferLength: partialUpdateBuffer.length,
        contentLength: artifact.content.length
      });
      return (
        artifact.content.substring(0, start) +
        partialUpdateBuffer +
        artifact.content.substring(end)
      );
    }
    
    // Otherwise use artifact from context or fall back to message
    return artifact?.content || message.content;
  }, [artifact, message.content, isPartialUpdateActive, partialUpdateBuffer, partialUpdateSelection]);

  const handleCopy = () => {
    navigator.clipboard.writeText(displayContent);
  };

  const handleDownload = () => {
    const extension = message.artifactType === 'code' 
      ? message.language || 'txt'
      : 'md';
    const blob = new Blob([displayContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${message.title || 'artifact'}.${extension}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const Icon = message.artifactType === 'code' ? FileCode : FileText;
  const isStreaming = message.isStreaming || isPartialUpdateActive;

  return (
    <Card className="flex flex-col h-full border-0 rounded-none shadow-none">
      <CardHeader className="flex-none bg-muted/30 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">
              {message.title || 'Artifact'}
            </CardTitle>
            {isStreaming && (
              <span className="text-xs text-muted-foreground animate-pulse">
                {isPartialUpdateActive ? 'Updating...' : 'Streaming...'}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              title="Copy to clipboard"
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              title="Download"
            >
              <Download className="h-4 w-4" />
            </Button>
            {onClose && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                title="Close artifact panel"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        {message.artifactType === 'code' && message.language && (
          <p className="text-sm text-muted-foreground mt-1">
            Language: {message.language}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex-1 min-h-0 overflow-hidden p-0">
        <ScrollArea className="h-full w-full">
          <div className="p-4">
            {message.artifactType === 'code' ? (
              <CodeRenderer
                code={displayContent}
                language={message.language || 'text'}
                isStreaming={isStreaming}
                onUpdate={() => {}} // Read-only for now
              />
            ) : (
              <TextRenderer
                markdown={displayContent}
                isStreaming={isStreaming}
                onUpdate={() => {}} // Read-only for now
                onSelectionChange={handleSelectionChange}
              />
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
