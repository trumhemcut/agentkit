'use client';

import { Message } from '@/types/chat';
import { UserMessageBubble } from './UserMessageBubble';
import { AgentMessageBubble } from './AgentMessageBubble';

interface MessageBubbleProps {
  message: Message;
  onEnableCanvas?: (message: Message) => void;
  canvasModeActive?: boolean;
  threadId?: string | null;
  onActionEvent?: (event: any) => void;
  onRetry?: (messageId: string) => void;
}

/**
 * Message Bubble component
 * 
 * Routes to appropriate message bubble component based on message role
 */
export function MessageBubble({ message, onEnableCanvas, canvasModeActive, threadId, onActionEvent, onRetry }: MessageBubbleProps) {
  if (message.role === 'user') {
    return <UserMessageBubble message={message} canvasModeActive={canvasModeActive} />;
  }
  
  return (
    <AgentMessageBubble 
      message={message} 
      onEnableCanvas={onEnableCanvas} 
      canvasModeActive={canvasModeActive} 
      threadId={threadId}
      onActionEvent={onActionEvent}
      onRetry={onRetry}
    />
  );
}
