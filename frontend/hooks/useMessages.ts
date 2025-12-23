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
    
    if (threadId) {
      console.log('[useMessages] Adding message to thread:', threadId, message);
      StorageService.addMessage(threadId, message);
      console.log('[useMessages] Message added to localStorage');
    } else {
      console.warn('[useMessages] Cannot add message - threadId is null');
    }
    
    // Auto-scroll to bottom
    setTimeout(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }, 100);
  }, [threadId]); // Include threadId as dependency

  /**
   * Update an existing message
   */
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ));
    
    if (threadId) {
      console.log('[useMessages] Updating message in thread:', threadId, messageId, updates);
      StorageService.updateMessage(threadId, messageId, updates);
    } else {
      console.warn('[useMessages] Cannot update message - threadId is null');
    }
  }, [threadId]); // Include threadId as dependency

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
