'use client';

import { Message } from '@/types/chat';
import { UserMessageBubble } from './UserMessageBubble';
import { AgentMessageBubble } from './AgentMessageBubble';

interface MessageBubbleProps {
  message: Message;
}

/**
 * Message Bubble component
 * 
 * Routes to appropriate message bubble component based on message role
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'user') {
    return <UserMessageBubble message={message} />;
  }
  
  return <AgentMessageBubble message={message} />;
}
