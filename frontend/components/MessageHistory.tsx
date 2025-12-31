'use client';

import { MessageBubble } from './MessageBubble';
import { Message } from '@/types/chat';
import { MessageSquare } from 'lucide-react';
import { RefObject } from 'react';

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
  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center">
        <MessageSquare className="mb-4 h-12 w-12 text-muted-foreground" />
        <h3 className="mb-2 text-lg font-semibold">No messages yet</h3>
        <p className="text-sm text-muted-foreground">
          Start a conversation by typing a message below
        </p>
      </div>
    );
  }

  return (
    <div 
      className="h-full overflow-y-auto p-4 space-y-4"
      ref={scrollRef}
      onScroll={onScroll}
    >
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
  );
}
