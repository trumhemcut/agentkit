'use client';

import { Message } from '@/types/chat';
import { UserMessageBubble } from './UserMessageBubble';
import { AgentMessageBubble } from './AgentMessageBubble';

interface MessageBubbleProps {
  message: Message;
  onEnableCanvas?: (message: Message) => void;
}

/**
 * Message Bubble component
 * 
 * Routes to appropriate message bubble component based on message role
 */
export function MessageBubble({ message, onEnableCanvas }: MessageBubbleProps) {
  if (message.role === 'user') {
    return <UserMessageBubble message={message} />;
  }
  
  return <AgentMessageBubble message={message} onEnableCanvas={onEnableCanvas} />;
}
