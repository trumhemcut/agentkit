'use client';

import { useState, useEffect, useCallback } from 'react';
import { Message, isArtifactMessage } from '@/types/chat';
import { StorageService } from '@/services/storage';
import { useAutoScroll } from './useAutoScroll';

export interface UseMessagesOptions {
  onArtifactDetected?: (message: Message) => void;
}

/**
 * Hook for managing messages in a thread
 * 
 * Handles message state, updates, and auto-scrolling.
 * Detects artifact messages and triggers canvas mode.
 * Phase 1: Syncs messages to server in background while maintaining LocalStorage as primary source.
 */
export function useMessages(threadId: string | null, options?: UseMessagesOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Use auto-scroll hook with messages as dependency
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

    // Mark as initial load when loading thread messages
    setIsInitialLoad(true);
    
    const thread = StorageService.getThread(threadId);
    if (thread) {
      setMessages(thread.messages);
    } else {
      setMessages([]);
    }
    
    // After messages are loaded and rendered, mark initial load as complete
    // Use a small delay to allow rendering to complete
    setTimeout(() => {
      setIsInitialLoad(false);
    }, 100);
  }, [threadId]);

  /**
   * Update message ID (replace temp frontend ID with backend ID)
   * Phase 1: Updates message ID in state and localStorage after backend sync
   */
  const updateMessageId = useCallback((tempId: string, backendId: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === tempId ? { ...msg, id: backendId } : msg
    ));
    
    if (threadId) {
      console.log('[useMessages] Updating message ID:', tempId, '→', backendId);
      StorageService.updateMessageId(threadId, tempId, backendId);
    }
  }, [threadId]);

  /**
   * Add a new message
   * Phase 1: Adds locally and syncs to server in background, then updates with backend ID
   */
  const addMessage = useCallback((message: Message) => {
    const tempId = message.id;
    setMessages(prev => [...prev, message]);
    
    // Detect artifact messages and defer callback to avoid setState during render
    if (isArtifactMessage(message) && options?.onArtifactDetected) {
      // Use queueMicrotask to defer execution until after render
      queueMicrotask(() => {
        options.onArtifactDetected?.(message);
      });
    }
    
    if (threadId) {
      console.log('[useMessages] Adding message to thread:', threadId, message);
      StorageService.addMessage(threadId, message);
      console.log('[useMessages] Message added to localStorage');
      
      // Phase 1: Sync to server in background (non-blocking)
      // If message is ready (not pending/streaming), sync immediately and update ID
      if (!message.isPending && !message.isStreaming) {
        StorageService.syncMessageToServer(threadId, message)
          .then(backendMessage => {
            if (backendMessage && backendMessage.id !== tempId) {
              console.log('[useMessages] Updating message ID after sync:', tempId, '→', backendMessage.id);
              updateMessageId(tempId, backendMessage.id);
            }
          })
          .catch(error => {
            console.error('[useMessages] Failed to sync message:', error);
            // Keep temp ID on error
          });
      }
    } else {
      console.warn('[useMessages] Cannot add message - threadId is null');
    }
  }, [threadId, options, updateMessageId]); // Include updateMessageId as dependency

  /**
   * Update an existing message
   * Phase 1: Updates locally and syncs to server when message is complete, then updates ID
   */
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    const tempId = messageId;
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const updatedMsg = { ...msg, ...updates };
        
        // If this is an artifact message being updated, defer callback to avoid setState during render
        if (isArtifactMessage(updatedMsg) && options?.onArtifactDetected) {
          // Use queueMicrotask to defer execution until after render
          queueMicrotask(() => {
            options.onArtifactDetected?.(updatedMsg);
          });
        }
        
        return updatedMsg;
      }
      return msg;
    }));
    
    if (threadId) {
      console.log('[useMessages] Updating message in thread:', threadId, messageId, updates);
      StorageService.updateMessage(threadId, messageId, updates);
      
      // Phase 1: Sync to server if message is now complete (no longer pending/streaming)
      if (updates.isPending === false || updates.isStreaming === false) {
        // Get the updated message to sync
        const thread = StorageService.getThread(threadId);
        const updatedMsg = thread?.messages.find(m => m.id === messageId);
        if (updatedMsg && !updatedMsg.isPending && !updatedMsg.isStreaming) {
          console.log('[useMessages] Message completed, syncing to server');
          StorageService.syncMessageToServer(threadId, updatedMsg)
            .then(backendMessage => {
              if (backendMessage && backendMessage.id !== tempId) {
                console.log('[useMessages] Updating message ID after sync:', tempId, '→', backendMessage.id);
                updateMessageId(tempId, backendMessage.id);
              }
            })
            .catch(error => {
              console.error('[useMessages] Failed to sync message:', error);
              // Keep temp ID on error
            });
        }
      }
    } else {
      console.warn('[useMessages] Cannot update message - threadId is null');
    }
  }, [threadId, options, updateMessageId]); // Include updateMessageId as dependency

  /**
   * Remove a message
   */
  const removeMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
    
    if (threadId) {
      console.log('[useMessages] Removing message from thread:', threadId, messageId);
      const thread = StorageService.getThread(threadId);
      if (thread) {
        thread.messages = thread.messages.filter(msg => msg.id !== messageId);
        StorageService.saveThread(thread);
      }
    } else {
      console.warn('[useMessages] Cannot remove message - threadId is null');
    }
  }, [threadId]);

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
