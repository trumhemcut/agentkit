'use client';

import { useState, useEffect, useCallback } from 'react';
import { Thread } from '@/types/chat';
import { StorageService } from '@/services/storage';

/**
 * Hook for managing chat threads
 * 
 * Provides thread CRUD operations and state management.
 * Phase 1: Syncs threads to server in background while maintaining LocalStorage as primary source.
 * 
 * @param initialThreadId - Optional thread ID from URL params to initialize with
 * @param agentId - Agent ID for server sync (default: 'chat')
 * @param model - Model for server sync (default: 'qwen:7b')
 * @param provider - Provider for server sync (default: 'ollama')
 */
export function useChatThreads(
  initialThreadId?: string,
  agentId: string = 'chat',
  model: string = 'qwen:7b',
  provider: string = 'ollama'
) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load threads from localStorage on mount
  useEffect(() => {
    const loadedThreads = StorageService.getThreads();
    setThreads(loadedThreads);
    
    // Auto-create first thread if no threads exist
    if (loadedThreads.length === 0) {
      const newThread: Thread = {
        id: crypto.randomUUID(),
        title: 'New Chat',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      StorageService.saveThread(newThread);
      setThreads([newThread]);
      setCurrentThreadId(newThread.id);
    } else if (initialThreadId) {
      // If initialThreadId provided from URL, use it
      const threadExists = loadedThreads.some(t => t.id === initialThreadId);
      setCurrentThreadId(threadExists ? initialThreadId : loadedThreads[0].id);
    } else {
      // Select the most recent thread
      setCurrentThreadId(loadedThreads[0].id);
    }
    
    setIsLoading(false);
  }, [initialThreadId]);

  /**
   * Create a new thread
   * Uses server-authoritative ID generation:
   * 1. Creates temporary thread for optimistic UI
   * 2. Syncs to server and gets authoritative ID
   * 3. Replaces temp ID with server ID
   */
  const createThread = useCallback(async () => {
    // Step 1: Create temporary thread for optimistic UI
    const tempId = crypto.randomUUID();
    const tempThread: Thread = {
      id: tempId,
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    StorageService.saveThread(tempThread);
    setThreads(StorageService.getThreads());
    setCurrentThreadId(tempId);
    
    // Step 2: Sync to server and get authoritative ID
    try {
      const serverThread = await StorageService.syncThreadToServer(
        tempThread, 
        agentId, 
        model, 
        provider
      );
      
      // Step 3: Replace temp ID with server ID
      StorageService.deleteThread(tempId);
      const finalThread: Thread = {
        ...tempThread,
        id: serverThread.id,
        createdAt: new Date(serverThread.created_at).getTime(),
        updatedAt: new Date(serverThread.updated_at).getTime(),
      };
      StorageService.saveThread(finalThread);
      setThreads(StorageService.getThreads());
      setCurrentThreadId(serverThread.id);
      
      console.log('[useChatThreads] ✅ Thread created with server ID:', serverThread.id);
      return finalThread;
    } catch (error) {
      console.error('[useChatThreads] ⚠️ Failed to sync thread to server:', error);
      // Keep temp thread and show warning to user
      console.warn('[useChatThreads] Using temporary thread ID (offline mode):', tempId);
      return tempThread;
    }
  }, [agentId, model, provider]);

  /**
   * Delete a thread
   * Phase 1: Deletes locally and syncs to server in background
   */
  const deleteThread = useCallback((threadId: string) => {
    StorageService.deleteThread(threadId);
    setThreads(prev => prev.filter(t => t.id !== threadId));
    
    // Phase 1: Sync deletion to server in background (non-blocking)
    StorageService.syncThreadDeleteToServer(threadId);
    
    if (currentThreadId === threadId) {
      setCurrentThreadId(null);
    }
  }, [currentThreadId]);

  /**
   * Select a thread
   */
  const selectThread = useCallback((threadId: string) => {
    setCurrentThreadId(threadId);
  }, []);

  /**
   * Update thread title
   * Phase 1: Updates locally and syncs to server in background
   */
  const updateThreadTitle = useCallback((threadId: string, title: string) => {
    // Get thread from localStorage to ensure we have the latest messages
    const thread = StorageService.getThread(threadId);
    if (thread) {
      const updatedThread = { ...thread, title, updatedAt: Date.now() };
      StorageService.saveThread(updatedThread);
      // Reload threads to maintain sort order
      setThreads(StorageService.getThreads());
      
      // Phase 1: Sync title to server in background (non-blocking)
      StorageService.syncThreadTitleToServer(threadId, title);
    }
  }, []);

  /**
   * Get current thread
   */
  const currentThread = threads.find(t => t.id === currentThreadId) || null;

  /**
   * Refresh threads from storage
   */
  const refreshThreads = useCallback(() => {
    const loadedThreads = StorageService.getThreads();
    setThreads(loadedThreads);
  }, []);

  return {
    threads,
    currentThread,
    currentThreadId,
    isLoading,
    createThread,
    deleteThread,
    selectThread,
    updateThreadTitle,
    refreshThreads,
  };
}
