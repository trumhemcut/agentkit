"use client";

import { Message, isArtifactMessage } from '@/types/chat';
import { CodeRenderer } from './Canvas/CodeRenderer';
import { TextRenderer } from './Canvas/TextRenderer';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Copy, Download, FileCode, FileText, X } from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';

interface ArtifactPanelProps {
  message: Message;
  onClose?: () => void;
}

/**
 * ArtifactPanel component
 * Displays artifact messages (code or text) in a dedicated panel
 */
export function ArtifactPanel({ message, onClose }: ArtifactPanelProps) {
  if (!isArtifactMessage(message)) {
    console.warn('ArtifactPanel received non-artifact message');
    return null;
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
  };

  const handleDownload = () => {
    const extension = message.artifactType === 'code' 
      ? message.language || 'txt'
      : 'md';
    const blob = new Blob([message.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${message.title || 'artifact'}.${extension}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const Icon = message.artifactType === 'code' ? FileCode : FileText;

  return (
    <Card className="flex flex-col h-full border-0 rounded-none shadow-none">
      <CardHeader className="flex-none border-b bg-muted/30 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">
              {message.title || 'Artifact'}
            </CardTitle>
            {message.isStreaming && (
              <span className="text-xs text-muted-foreground animate-pulse">
                Streaming...
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
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full">
          {message.artifactType === 'code' ? (
            <CodeRenderer
              code={message.content}
              language={message.language || 'text'}
              isStreaming={message.isStreaming || false}
              onUpdate={() => {}} // Read-only for now
            />
          ) : (
            <TextRenderer
              markdown={message.content}
              isStreaming={message.isStreaming || false}
              onUpdate={() => {}} // Read-only for now
            />
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
