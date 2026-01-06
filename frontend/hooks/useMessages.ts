'use client';

import { useState, useEffect, useCallback } from 'react';
import { Message, isArtifactMessage } from '@/types/chat';
import { useMessageStore } from '@/stores/messageStore';
import { useAutoScroll } from './useAutoScroll';

export interface UseMessagesOptions {
  onArtifactDetected?: (message: Message) => void;
}

/**
 * Hook for managing messages in a thread (now database-first)
 */
export function useMessages(threadId: string | null, options?: UseMessagesOptions) {
  const {
    messagesByThread,
    isLoadingMessages,
    loadMessages,
    addMessage: addMessageStore,
    updateMessage: updateMessageStore,
    getMessages,
  } = useMessageStore();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  
  // Use auto-scroll hook
  const { scrollRef, handleScroll, scrollToBottom, shouldAutoScroll } = useAutoScroll(
    [messages],
    { isInitialLoad }
  );
  
  // Load messages when thread changes
  useEffect(() => {
    if (!threadId) {
      setMessages([]);
      setIsInitialLoad(true);
      return;
    }
    
    setIsInitialLoad(true);
    setIsLoading(true);
    
    // Load from store
    loadMessages(threadId).then(() => {
      const threadMessages = getMessages(threadId);
      setMessages(threadMessages);
      setIsLoading(false);
      
      setTimeout(() => {
        setIsInitialLoad(false);
      }, 100);
    });
  }, [threadId, loadMessages, getMessages]);
  
  // Update local messages when store changes
  useEffect(() => {
    if (threadId && messagesByThread[threadId]) {
      setMessages(messagesByThread[threadId]);
    }
  }, [threadId, messagesByThread]);
  
  /**
   * Add a new message
   */
  const addMessage = useCallback((message: Message) => {
    console.log('[useMessages] Adding message:', message.id, message.role, message.isPending);
    
    // Update local state for immediate UI
    setMessages(prev => {
      // Check if message already exists in local state
      if (prev.some(m => m.id === message.id)) {
        console.warn('[useMessages] Message already exists in local state:', message.id);
        return prev;
      }
      return [...prev, message];
    });
    
    // Detect artifact messages
    if (isArtifactMessage(message) && options?.onArtifactDetected) {
      queueMicrotask(() => {
        options.onArtifactDetected?.(message);
      });
    }
    
    if (threadId) {
      // Sync to database
      addMessageStore(threadId, message);
    }
  }, [threadId, addMessageStore, options]);
  
  /**
   * Update message (for streaming)
   */
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    console.log('[useMessages.updateMessage] Called with:', messageId, updates);
    
    // Update local state
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const updatedMsg = { ...msg, ...updates };
        
        // Detect artifact messages
        if (isArtifactMessage(updatedMsg) && options?.onArtifactDetected) {
          queueMicrotask(() => {
            options.onArtifactDetected?.(updatedMsg);
          });
        }
        
        return updatedMsg;
      }
      return msg;
    }));
    
    if (threadId) {
      // Update in store
      updateMessageStore(threadId, messageId, updates);
      
      // If agent message is complete OR interrupted, sync to database
      // Note: Only agent messages need this because they start as pending/streaming
      // User messages are already saved when first created
      if (updates.isPending === false || updates.isStreaming === false || updates.isInterrupted === true) {
        const completedMessage = messages.find(m => m.id === messageId);
        if (completedMessage && completedMessage.role === 'agent') {
          console.log('[useMessages] Syncing completed/interrupted agent message to database:', messageId);
          addMessageStore(threadId, { ...completedMessage, ...updates }, updates.isInterrupted === true || updates.isStreaming === false);
        }
      }
    }
  }, [threadId, messages, updateMessageStore, addMessageStore, options]);
  
  /**
   * Update message ID (for backend sync)
   */
  const updateMessageId = useCallback((tempId: string, backendId: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === tempId ? { ...msg, id: backendId } : msg
    ));
    
    if (threadId) {
      updateMessageStore(threadId, tempId, { id: backendId });
    }
  }, [threadId, updateMessageStore]);
  
  /**
   * Remove a message
   */
  const removeMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
    
    if (threadId) {
      // Filter from store
      const filtered = getMessages(threadId).filter(m => m.id !== messageId);
      updateMessageStore(threadId, messageId, { id: '' }); // Mark for removal
    }
  }, [threadId, getMessages, updateMessageStore]);
  
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
    updateMessageId,
    removeMessage,
    clearMessages,
    scrollToBottom,
    scrollRef,
    handleScroll,
    shouldAutoScroll,
  };
}
