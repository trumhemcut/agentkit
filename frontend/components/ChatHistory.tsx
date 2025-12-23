'use client';

import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageBubble } from './MessageBubble';
import { Message } from '@/types/chat';
import { MessageSquare } from 'lucide-react';
import { RefObject } from 'react';

interface ChatHistoryProps {
  messages: Message[];
  scrollRef?: RefObject<HTMLDivElement | null>;
}

/**
 * Chat History component
 * 
 * Displays list of messages with auto-scroll
 */
export function ChatHistory({ messages, scrollRef }: ChatHistoryProps) {
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
    <ScrollArea className="h-full">
      <div ref={scrollRef}>
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>
    </ScrollArea>
  );
}
