'use client';

import { useState, useEffect, useCallback } from 'react';
import { Thread } from '@/types/chat';
import { StorageService } from '@/services/storage';

/**
 * Hook for managing chat threads
 * 
 * Provides thread CRUD operations and state management
 * 
 * @param initialThreadId - Optional thread ID from URL params to initialize with
 */
export function useChatThreads(initialThreadId?: string) {
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
        id: `thread-${Date.now()}`,
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
   */
  const createThread = useCallback(() => {
    const newThread: Thread = {
      id: `thread-${Date.now()}`,
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    StorageService.saveThread(newThread);
    // Reload threads to maintain sort order
    setThreads(StorageService.getThreads());
    setCurrentThreadId(newThread.id);
    
    return newThread;
  }, []);

  /**
   * Delete a thread
   */
  const deleteThread = useCallback((threadId: string) => {
    StorageService.deleteThread(threadId);
    setThreads(prev => prev.filter(t => t.id !== threadId));
    
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
   */
  const updateThreadTitle = useCallback((threadId: string, title: string) => {
    // Get thread from localStorage to ensure we have the latest messages
    const thread = StorageService.getThread(threadId);
    if (thread) {
      const updatedThread = { ...thread, title, updatedAt: Date.now() };
      StorageService.saveThread(updatedThread);
      // Reload threads to maintain sort order
      setThreads(StorageService.getThreads());
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
