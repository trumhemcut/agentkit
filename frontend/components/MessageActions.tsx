'use client';

import { Button } from '@/components/ui/button';
import { 
  ThumbsUp, 
  ThumbsDown, 
  Copy, 
  RotateCw 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  submitMessageFeedback, 
  removeMessageFeedback, 
  getMessageFeedback 
} from '@/services/api';

interface MessageActionsProps {
  messageId: string;
  messageContent: string;
  onRetry?: () => void;
  className?: string;
  initialFeedback?: 'like' | 'dislike' | null;
}

/**
 * MessageActions component
 * 
 * Provides interactive actions for agent messages:
 * - Copy: Copy message content to clipboard
 * - Like: Submit positive feedback
 * - Dislike: Submit negative feedback
 * - Retry: Regenerate the response
 */
export function MessageActions({ 
  messageId, 
  messageContent, 
  onRetry,
  className,
  initialFeedback = null
}: MessageActionsProps) {
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(initialFeedback);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load feedback state from backend on mount
  useEffect(() => {
    const loadFeedback = async () => {
      try {
        const data = await getMessageFeedback(messageId);
        setFeedback(data.feedback_type);
      } catch (error) {
        console.error('Failed to load feedback:', error);
      }
    };
    
    loadFeedback();
  }, [messageId]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(messageContent);
      toast.success('Copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy');
    }
  };

  const handleFeedback = async (type: 'like' | 'dislike') => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      // If clicking the same feedback, remove it
      if (feedback === type) {
        await removeMessageFeedback(messageId);
        setFeedback(null);
      } else {
        // Submit new feedback
        await submitMessageFeedback(messageId, type);
        setFeedback(type);
      }
    } catch (error) {
      toast.error('Failed to submit feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {/* Copy Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleCopy}
        className="h-8 w-8 p-0 hover:bg-muted"
        title="Copy message"
      >
        <Copy className="h-4 w-4" />
      </Button>

      {/* Like Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback('like')}
        disabled={isSubmitting}
        className={cn(
          "h-8 w-8 p-0 hover:bg-muted",
          feedback === 'like' && "bg-muted text-green-600"
        )}
        title="Good response"
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>

      {/* Dislike Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback('dislike')}
        disabled={isSubmitting}
        className={cn(
          "h-8 w-8 p-0 hover:bg-muted",
          feedback === 'dislike' && "bg-muted text-red-600"
        )}
        title="Bad response"
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>

      {/* Retry Button */}
      {onRetry && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onRetry}
          className="h-8 w-8 p-0 hover:bg-muted"
          title="Regenerate response"
        >
          <RotateCw className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
