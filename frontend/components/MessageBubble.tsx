'use client';

import { Message } from '@/types/chat';
import { Card, CardContent } from '@/components/ui/card';
import { AvatarIcon } from './AvatarIcon';
import { cn } from '@/lib/utils';

interface MessageBubbleProps {
  message: Message;
}

/**
 * Message Bubble component
 * 
 * Displays a single chat message with avatar and content
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={cn(
      "flex gap-3 p-4",
      message.role === 'user' ? 'justify-end' : 'justify-start'
    )}>
      {message.role === 'agent' && (
        <AvatarIcon role="agent" />
      )}
      
      <div className={cn(
        "flex flex-col gap-1 max-w-[70%]",
        message.role === 'user' && 'items-end'
      )}>
        {message.role === 'agent' && message.agentName && (
          <span className="text-xs font-medium text-muted-foreground">
            {message.agentName}
          </span>
        )}
        
        <Card className={cn(
          message.role === 'user' 
            ? 'bg-primary text-primary-foreground' 
            : 'bg-muted'
        )}>
          <CardContent className="p-3">
            <p className="text-sm whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </CardContent>
        </Card>
        
        <span className="text-xs text-muted-foreground">
          {formatTime(message.timestamp)}
        </span>
      </div>

      {message.role === 'user' && (
        <AvatarIcon role="user" />
      )}
    </div>
  );
}
