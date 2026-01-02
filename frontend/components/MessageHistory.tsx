'use client';

import { MessageBubble } from './MessageBubble';
import { Message } from '@/types/chat';
import { MessageSquare } from 'lucide-react';
import { RefObject } from 'react';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/lib/utils';

interface MessageHistoryProps {
  messages: Message[];
  scrollRef?: RefObject<HTMLDivElement | null>;
  onEnableCanvas?: (message: Message) => void;
  onScroll?: () => void;
  canvasModeActive?: boolean;
  threadId?: string | null;
  onActionEvent?: (event: any) => void;
}

/**
 * Message History component
 * 
 * Displays list of messages with auto-scroll and A2UI surfaces
 */
export function MessageHistory({ messages, scrollRef, onEnableCanvas, onScroll, canvasModeActive, threadId, onActionEvent }: MessageHistoryProps) {
  const isMobile = useIsMobile();
  
  if (messages.length === 0) {
    return null; // Empty state handled by ChatContainer
  }

  return (
    <div 
      className="h-full overflow-y-auto w-full"
      ref={scrollRef}
      onScroll={onScroll}
    >
      <div className={cn(
        // Mobile: smaller padding and spacing, full width
        // Desktop: constrained width and centered
        isMobile ? "p-2 space-y-1 w-full" : "p-4 space-y-4 max-w-[800px] mx-auto w-full"
      )}>
        {messages.map((message) => (
          <MessageBubble 
            key={message.id} 
            message={message} 
            onEnableCanvas={onEnableCanvas} 
            canvasModeActive={canvasModeActive} 
            threadId={threadId}
            onActionEvent={onActionEvent}
          />
        ))}
      </div>
    </div>
  );
}
