import { create } from 'zustand';
import { Thread } from '@/types/database';
import { threadsApi } from '@/services/api';
import { toast } from 'sonner';

interface ThreadState {
  // State
  threads: Thread[];
  currentThreadId: string | null;
  isLoading: boolean;
  isInitialized: boolean;
  
  // Actions
  loadThreads: () => Promise<void>;
  createThread: (agentId: string, model: string, provider: string) => Promise<Thread | null>;
  selectThread: (threadId: string) => void;
  updateThreadTitle: (threadId: string, title: string) => Promise<void>;
  deleteThread: (threadId: string) => Promise<void>;
  getThread: (threadId: string) => Thread | null;
}

export const useThreadStore = create<ThreadState>((set, get) => ({
  // Initial state
  threads: [],
  currentThreadId: null,
  isLoading: false,
  isInitialized: false,
  
  /**
   * Load all threads from database
   */
  loadThreads: async () => {
    const { isLoading, isInitialized } = get();
    
    // Prevent duplicate loads
    if (isLoading || isInitialized) return;
    
    set({ isLoading: true });
    
    try {
      const response = await threadsApi.list();
      const threads = response.threads || [];
      
      set({ 
        threads,
        isLoading: false,
        isInitialized: true,
        // Select first thread if none selected
        currentThreadId: threads.length > 0 ? threads[0].id : null
      });
      
      console.log('[ThreadStore] Loaded threads:', threads.length);
    } catch (error) {
      console.error('[ThreadStore] Failed to load threads:', error);
      toast.error('Failed to load threads');
      set({ isLoading: false, isInitialized: true });
    }
  },
  
  /**
   * Create new thread (database-first)
   */
  createThread: async (agentId: string, model: string, provider: string) => {
    try {
      // Show loading toast
      const toastId = toast.loading('Creating new chat...');
      
      // Create in database
      const newThread = await threadsApi.create({
        title: 'New Chat',
        agent_id: agentId,
        model,
        provider,
      });
      
      // Update store
      set(state => ({
        threads: [newThread, ...state.threads],
        currentThreadId: newThread.id,
      }));
      
      toast.success('New chat created', { id: toastId });
      console.log('[ThreadStore] Created thread:', newThread.id);
      
      return newThread;
    } catch (error) {
      console.error('[ThreadStore] Failed to create thread:', error);
      toast.error('Failed to create chat');
      return null;
    }
  },
  
  /**
   * Select thread
   */
  selectThread: (threadId: string) => {
    set({ currentThreadId: threadId });
  },
  
  /**
   * Update thread title (optimistic update)
   */
  updateThreadTitle: async (threadId: string, title: string) => {
    // Optimistic update
    set(state => ({
      threads: state.threads.map(t => 
        t.id === threadId 
          ? { ...t, title, updated_at: new Date().toISOString() }
          : t
      ),
    }));
    
    try {
      // Sync to database
      await threadsApi.update(threadId, { title });
      console.log('[ThreadStore] Updated thread title:', threadId);
    } catch (error) {
      console.error('[ThreadStore] Failed to update title:', error);
      toast.error('Failed to update title');
      // Revert on error
      get().loadThreads();
    }
  },
  
  /**
   * Delete thread (optimistic update)
   */
  deleteThread: async (threadId: string) => {
    // Optimistic update
    const prevThreads = get().threads;
    const prevCurrentId = get().currentThreadId;
    
    set(state => {
      const newThreads = state.threads.filter(t => t.id !== threadId);
      return {
        threads: newThreads,
        currentThreadId: state.currentThreadId === threadId 
          ? (newThreads[0]?.id || null)
          : state.currentThreadId,
      };
    });
    
    try {
      // Sync to database
      await threadsApi.delete(threadId);
      toast.success('Chat deleted');
      console.log('[ThreadStore] Deleted thread:', threadId);
    } catch (error) {
      console.error('[ThreadStore] Failed to delete thread:', error);
      toast.error('Failed to delete chat');
      // Revert on error
      set({ threads: prevThreads, currentThreadId: prevCurrentId });
    }
  },
  
  /**
   * Get thread by ID
   */
  getThread: (threadId: string) => {
    return get().threads.find(t => t.id === threadId) || null;
  },
}));
