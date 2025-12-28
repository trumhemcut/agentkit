'use client';

import { Message } from '@/types/chat';
import { Card, CardContent } from '@/components/ui/card';
import { AvatarIcon } from './AvatarIcon';

interface UserMessageBubbleProps {
  message: Message;
  canvasModeActive?: boolean;
}

/**
 * User Message Bubble component
 * 
 * Displays a user chat message with avatar and plain text content
 */
export function UserMessageBubble({ message, canvasModeActive }: UserMessageBubbleProps) {
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`flex p-4 justify-end ${canvasModeActive ? 'gap-0' : 'gap-3'}`}>
      <div className="flex flex-col gap-1 max-w-[70%] items-end">
        <Card className="border-0 py-0" style={{ backgroundColor: '#F4F4F4' }}>
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

      {!canvasModeActive && <AvatarIcon role="user" />}
    </div>
  );
}
