'use client';

import { Message, isArtifactMessage } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { AvatarIcon } from './AvatarIcon';
import { cn, generateUniqueId } from '@/lib/utils';
import { Loader2, Edit } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { A2UIRenderer } from './A2UI/A2UIRenderer';
import { useA2UIStore } from '@/stores/a2uiStore';
import { useModelStore } from '@/stores/modelStore';
import { a2uiManager } from '@/lib/a2ui/A2UIManager';
import { A2UIUserActionService } from '@/services/a2uiActionService';
import { InsuranceSupervisorIndicator } from './InsuranceSupervisorIndicator';
import { MessageActions } from './MessageActions';
import { useEffect, useMemo } from 'react';
import { useIsMobile } from '@/hooks/useMediaQuery';
import type { UserAction } from '@/types/a2ui';

interface AgentMessageBubbleProps {
  message: Message;
  onEnableCanvas?: (message: Message) => void;
  canvasModeActive?: boolean;
  threadId?: string | null;
  agentId?: string;
  onActionEvent?: (event: any) => void;
  onRetry?: (messageId: string) => void;
}

/**
 * Agent Message Bubble component
 * 
 * Displays an agent chat message with avatar and markdown-rendered content
 */
export function AgentMessageBubble({ 
  message, 
  onEnableCanvas, 
  canvasModeActive, 
  threadId,
  agentId, // Can be passed explicitly, but will use message.agentId if available
  onActionEvent,
  onRetry
}: AgentMessageBubbleProps) {
  // Subscribe to surfaces map to trigger re-renders when surfaces change
  const surfaces = useA2UIStore((state) => state.surfaces);
  const getSurfacesByMessageId = useA2UIStore((state) => state.getSurfacesByMessageId);
  
  // Get current model and provider from model store
  const selectedModel = useModelStore((state) => state.selectedModel);
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  
  // Get surfaces for this message (for rendering)
  const messageSurfaces = getSurfacesByMessageId(message.id);
  
  // Determine which agent ID to use: message.agentId > agentId prop > default
  const effectiveAgentId = message.agentId || agentId || 'a2ui-loop';
  
  // Mobile detection
  const isMobile = useIsMobile();
  
  // Setup action handler for this message's surfaces using a2uiManager
  useEffect(() => {
    // Get surfaces inside effect to ensure we have latest state
    const currentSurfaces = getSurfacesByMessageId(message.id);
    
    console.log('[AgentMessageBubble] Setting up action handlers', {
      messageId: message.id,
      threadId,
      effectiveAgentId,
      surfaceCount: currentSurfaces.length,
      surfaces: currentSurfaces.map(s => ({ id: s.id, hasRoot: !!s.rootComponentId }))
    });
    
    if (!threadId || currentSurfaces.length === 0) {
      console.log('[AgentMessageBubble] Skipping action handler setup - missing threadId or no surfaces');
      return;
    }
    
    const handleUserAction = async (action: UserAction) => {
      console.log('[AgentMessageBubble] User action triggered:', action);
      
      // Generate new run ID for this action
      const runId = generateUniqueId('run');
      
      try {
        // Send action to backend and process SSE stream
        await A2UIUserActionService.sendAction(
          effectiveAgentId,
          action,
          threadId,
          runId,
          (event) => {
            console.log('[AgentMessageBubble] Received event from action:', event.type);
            // Forward event to parent handler if provided
            if (onActionEvent) {
              onActionEvent(event);
            }
          },
          selectedModel || undefined,
          selectedProvider || undefined
        );
      } catch (error) {
        console.error('[AgentMessageBubble] Error processing user action:', error);
      }
    };
    
    // Register action handler for all surfaces in this message
    currentSurfaces.forEach(surface => {
      console.log('[AgentMessageBubble] Registering action handler for surface:', surface.id);
      a2uiManager.onAction(surface.id, handleUserAction);
    });
    
    // Cleanup on unmount
    return () => {
      // Note: Currently no cleanup method in a2uiManager
      // Could add one if needed for memory management
    };
  }, [threadId, surfaces, effectiveAgentId, onActionEvent, message.id, getSurfacesByMessageId, selectedModel, selectedProvider]);
  
  // Legacy callback support (for backward compatibility)
  const handleA2UIAction = useMemo(() => {
    if (!threadId) return undefined;
    
    return (actionName: string, context: Record<string, any>) => {
      console.log('[AgentMessageBubble] Legacy A2UI action:', actionName, context);
      // This is the old pattern - can be kept for backward compatibility
      // or migrated to use a2uiManager as well
    };
  }, [threadId]);
  
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

  const handleRetry = () => {
    if (onRetry) {
      onRetry(message.id);
    }
  };

  const isThinking = (message.isPending || message.isStreaming) && message.content === '';
  
  // Check if this is an insurance supervisor message
  const isInsuranceSupervisor = message.agentId === 'insurance-supervisor';
  const selectedSpecialist = message.metadata?.selected_specialist as string | undefined;

  return (
    <div className={cn(
      "flex justify-start",
      // Mobile: smaller padding (py-2 px-3)
      // Desktop: normal padding (p-4)
      isMobile ? "py-2 px-3" : "p-4",
      // Full width for message content
      "w-full"
    )}>
      
      <div className={cn(
        "flex flex-col gap-1",
        // Full width for text content
        isThinking ? (isMobile ? "max-w-[70%]" : "max-w-[70%]") : "w-full"
      )}>
        {/* Show insurance supervisor indicator if applicable */}
        {isInsuranceSupervisor && !isThinking && (
          <div className="mb-2">
            <InsuranceSupervisorIndicator 
              specialist={selectedSpecialist}
              isActive={message.isStreaming}
            />
          </div>
        )}
        
        <div data-slot="card" className="flex flex-col bg-transparent py-0">
          <div data-slot="card-content" className="p-3">
            {isThinking ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">Thinking...</span>
              </div>
            ) : (
              <div className="text-sm markdown-content">
                {message.isInterrupted && (
                  <div className="mb-2 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md text-yellow-800 dark:text-yellow-200 text-xs">
                    ⚠️ Response interrupted by user
                  </div>
                )}
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
          </div>
        </div>
        
        {/* Show actions only for completed messages */}
        {!message.isPending && !message.isStreaming && (
          <div className="px-3">
            <MessageActions
              messageId={message.id}
              messageContent={message.content}
              onRetry={threadId ? handleRetry : undefined}
            />
          </div>
        )}
        
        {isArtifactMessage(message) && !message.isStreaming && (
          <div className="px-3 pb-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEnableCanvas}
              className="h-6 px-2 text-xs flex items-center gap-1"
            >
              <Edit className="h-3 w-3" />
              Edit in Canvas
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
