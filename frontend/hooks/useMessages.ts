'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Message } from '@/types/chat';
import { StorageService } from '@/services/storage';

/**
 * Hook for managing messages in a thread
 * 
 * Handles message state, updates, and auto-scrolling
 */
export function useMessages(threadId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Load messages when thread changes
  useEffect(() => {
    if (!threadId) {
      setMessages([]);
      return;
    }

    const thread = StorageService.getThread(threadId);
    if (thread) {
      setMessages(thread.messages);
    } else {
      setMessages([]);
    }
  }, [threadId]);

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  /**
   * Add a new message
   */
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
    
    const currentThreadId = threadId;
    if (currentThreadId) {
      StorageService.addMessage(currentThreadId, message);
    }
    
    // Auto-scroll to bottom
    setTimeout(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }, 100);
  }, []); // No dependencies - uses closure over threadId

  /**
   * Update an existing message
   */
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ));
    
    const currentThreadId = threadId;
    if (currentThreadId) {
      StorageService.updateMessage(currentThreadId, messageId, updates);
    }
  }, []); // No dependencies - uses closure over threadId

  /**
   * Clear all messages (for current thread)
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    addMessage,
    updateMessage,
    clearMessages,
    scrollToBottom,
    scrollRef,
  };
}
