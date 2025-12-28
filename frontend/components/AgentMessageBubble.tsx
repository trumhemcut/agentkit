'use client';

import { Message, isArtifactMessage } from '@/types/chat';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AvatarIcon } from './AvatarIcon';
import { cn } from '@/lib/utils';
import { Loader2, Edit } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { A2UIRenderer } from './A2UI/A2UIRenderer';
import { useA2UIStore } from '@/stores/a2uiStore';
import { a2uiActionService } from '@/services/a2uiActionService';
import { InsuranceSupervisorIndicator } from './InsuranceSupervisorIndicator';

interface AgentMessageBubbleProps {
  message: Message;
  onEnableCanvas?: (message: Message) => void;
  canvasModeActive?: boolean;
  threadId?: string | null;
}

/**
 * Agent Message Bubble component
 * 
 * Displays an agent chat message with avatar and markdown-rendered content
 */
export function AgentMessageBubble({ message, onEnableCanvas, canvasModeActive, threadId }: AgentMessageBubbleProps) {
  const getSurfacesByMessageId = useA2UIStore((state) => state.getSurfacesByMessageId);
  const messageSurfaces = getSurfacesByMessageId(message.id);
  
  // Create action callback for A2UI interactions
  const handleA2UIAction = a2uiActionService.createActionCallback(threadId || undefined);
  
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  const handleEnableCanvas = () => {
    onEnableCanvas?.(message);
  };

  const isThinking = (message.isPending || message.isStreaming) && message.content === '';
  
  // Check if this is an insurance supervisor message
  const isInsuranceSupervisor = message.agentId === 'insurance-supervisor';
  const selectedSpecialist = message.metadata?.selected_specialist as string | undefined;

  return (
    <div className={cn("flex p-4 justify-start", canvasModeActive ? "gap-0" : "gap-3")}>
      {!canvasModeActive && <AvatarIcon role="agent" />}
      
      <div className={cn("flex flex-col gap-1", !isThinking && canvasModeActive ? "flex-1" : "max-w-[70%]")}>
        {/* Show insurance supervisor indicator if applicable */}
        {isInsuranceSupervisor && !isThinking && (
          <div className="mb-2">
            <InsuranceSupervisorIndicator 
              specialist={selectedSpecialist}
              isActive={message.isStreaming}
            />
          </div>
        )}
        
        <Card className="bg-white border-0 py-0">
          <CardContent className="p-3">
            {isThinking ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">Thinking...</span>
              </div>
            ) : (
              <div className="text-sm markdown-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    code: ({ node, inline, className, children, ...props }: any) => {
                      return !inline ? (
                        <code className={cn(className, "block text-sm")} {...props}>
                          {children}
                        </code>
                      ) : (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                          {children}
                        </code>
                      );
                    },
                    pre: ({ children, ...props }: any) => (
                      <pre className="bg-slate-900 dark:bg-slate-950 text-slate-100 rounded-lg p-4 overflow-x-auto my-3 text-sm font-mono" {...props}>
                        {children}
                      </pre>
                    ),
                    a: ({ children, ...props }: any) => (
                      <a className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 underline" target="_blank" rel="noopener noreferrer" {...props}>
                        {children}
                      </a>
                    ),
                    p: ({ children, ...props }: any) => (
                      <p className="my-2 leading-relaxed" {...props}>
                        {children}
                      </p>
                    ),
                    h1: ({ children, ...props }: any) => (
                      <h1 className="text-xl font-bold my-3" {...props}>
                        {children}
                      </h1>
                    ),
                    h2: ({ children, ...props }: any) => (
                      <h2 className="text-lg font-bold my-3" {...props}>
                        {children}
                      </h2>
                    ),
                    h3: ({ children, ...props }: any) => (
                      <h3 className="text-base font-bold my-2" {...props}>
                        {children}
                      </h3>
                    ),
                    ul: ({ children, ...props }: any) => (
                      <ul className="list-disc list-inside my-2 space-y-1" {...props}>
                        {children}
                      </ul>
                    ),
                    ol: ({ children, ...props }: any) => (
                      <ol className="list-decimal list-inside my-2 space-y-1" {...props}>
                        {children}
                      </ol>
                    ),
                    li: ({ children, ...props }: any) => (
                      <li className="my-1" {...props}>
                        {children}
                      </li>
                    ),
                    blockquote: ({ children, ...props }: any) => (
                      <blockquote className="border-l-4 border-muted-foreground pl-4 my-2 italic" {...props}>
                        {children}
                      </blockquote>
                    ),
                    table: ({ children, ...props }: any) => (
                      <div className="overflow-x-auto my-3">
                        <table className="min-w-full border-collapse border border-border" {...props}>
                          {children}
                        </table>
                      </div>
                    ),
                    th: ({ children, ...props }: any) => (
                      <th className="border border-border bg-muted px-3 py-2 font-semibold text-left" {...props}>
                        {children}
                      </th>
                    ),
                    td: ({ children, ...props }: any) => (
                      <td className="border border-border px-3 py-2" {...props}>
                        {children}
                      </td>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
                
                {/* Render A2UI components for this message */}
                {messageSurfaces.length > 0 && (
                  <div className="mt-3">
                    {messageSurfaces.map((surface) => (
                      <A2UIRenderer key={surface.id} surfaceId={surface.id} onAction={handleA2UIAction} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
        
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
          
          {isArtifactMessage(message) && !message.isStreaming && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEnableCanvas}
              className="h-6 px-2 text-xs flex items-center gap-1"
            >
              <Edit className="h-3 w-3" />
              Edit in Canvas
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
