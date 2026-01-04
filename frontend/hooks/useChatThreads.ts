'use client';

import { useEffect } from 'react';
import { useThreadStore } from '@/stores/threadStore';

/**
 * Hook for managing chat threads (now database-first)
 * 
 * @param initialThreadId - Optional thread ID from URL params
 * @param agentId - Agent type for new threads (default: 'chat')
 * @param model - Model for new threads (default: 'qwen:7b')
 * @param provider - Provider for new threads (default: 'ollama')
 */
export function useChatThreads(
  initialThreadId?: string,
  agentId: string = 'chat',
  model: string = 'qwen:7b',
  provider: string = 'ollama'
) {
  const {
    threads,
    currentThreadId,
    isLoading,
    isInitialized,
    loadThreads,
    createThread: createThreadStore,
    selectThread,
    updateThreadTitle: updateTitleStore,
    deleteThread: deleteThreadStore,
    getThread,
  } = useThreadStore();
  
  // Load threads on mount
  useEffect(() => {
    if (!isInitialized) {
      loadThreads();
    }
  }, [isInitialized, loadThreads]);
  
  // Handle initial thread selection
  useEffect(() => {
    if (isInitialized && !currentThreadId && threads.length > 0) {
      if (initialThreadId && threads.some(t => t.id === initialThreadId)) {
        selectThread(initialThreadId);
      } else {
        selectThread(threads[0].id);
      }
    }
  }, [isInitialized, currentThreadId, initialThreadId, threads, selectThread]);
  
  // Auto-create first thread if no threads exist
  useEffect(() => {
    if (isInitialized && threads.length === 0) {
      createThreadStore(agentId, model, provider);
    }
  }, [isInitialized, threads.length, agentId, model, provider, createThreadStore]);
  
  // Get current thread
  const currentThread = currentThreadId ? getThread(currentThreadId) : null;
  
  return {
    threads,
    currentThread,
    currentThreadId,
    isLoading,
    createThread: () => createThreadStore(agentId, model, provider),
    deleteThread: deleteThreadStore,
    selectThread,
    updateThreadTitle: updateTitleStore,
    // Refresh threads is now handled by loadThreads
    refreshThreads: loadThreads,
  };
}
