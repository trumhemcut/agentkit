import { Thread, Message } from '@/types/chat';

const STORAGE_KEY = 'agentkit_threads';

/**
 * LocalStorage service for chat thread persistence
 */
export class StorageService {
  /**
   * Get all threads from localStorage
   * Returns threads sorted by updatedAt (newest first)
   */
  static getThreads(): Thread[] {
    if (typeof window === 'undefined') return [];
    
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      const threads = data ? JSON.parse(data) : [];
      // Sort by updatedAt descending (newest first)
      return threads.sort((a: Thread, b: Thread) => b.updatedAt - a.updatedAt);
    } catch (error) {
      console.error('Error reading threads from localStorage:', error);
      return [];
    }
  }

  /**
   * Get a specific thread by ID
   */
  static getThread(threadId: string): Thread | null {
    const threads = this.getThreads();
    const thread = threads.find(t => t.id === threadId) || null;
    console.log('[StorageService] getThread:', threadId, thread ? `found with ${thread.messages.length} messages` : 'NOT FOUND');
    return thread;
  }

  /**
   * Save a thread (create or update)
   */
  static saveThread(thread: Thread): void {
    if (typeof window === 'undefined') return;
    
    try {
      const threads = this.getThreads();
      const existingIndex = threads.findIndex(t => t.id === thread.id);
      
      console.log('[StorageService] saveThread:', thread.id, `with ${thread.messages.length} messages`, existingIndex >= 0 ? 'UPDATE' : 'CREATE');
      
      if (existingIndex >= 0) {
        threads[existingIndex] = { ...thread, updatedAt: Date.now() };
      } else {
        threads.push(thread);
      }
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
      console.log('[StorageService] Saved to localStorage successfully');
    } catch (error) {
      console.error('Error saving thread to localStorage:', error);
    }
  }

  /**
   * Delete a thread by ID
   */
  static deleteThread(threadId: string): void {
    if (typeof window === 'undefined') return;
    
    try {
      const threads = this.getThreads().filter(t => t.id !== threadId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
    } catch (error) {
      console.error('Error deleting thread from localStorage:', error);
    }
  }

  /**
   * Add a message to a thread
   */
  static addMessage(threadId: string, message: Message): void {
    console.log('[StorageService] addMessage called:', threadId, message.id);
    const thread = this.getThread(threadId);
    if (!thread) {
      console.error('[StorageService] Thread not found:', threadId);
      return;
    }
    
    console.log('[StorageService] Before push - thread has', thread.messages.length, 'messages');
    thread.messages.push(message);
    console.log('[StorageService] After push - thread has', thread.messages.length, 'messages');
    this.saveThread(thread);
  }

  /**
   * Update a message in a thread
   */
  static updateMessage(threadId: string, messageId: string, updates: Partial<Message>): void {
    console.log('[StorageService] updateMessage called:', threadId, messageId);
    const thread = this.getThread(threadId);
    if (!thread) {
      console.error('[StorageService] Thread not found for update:', threadId);
      return;
    }
    
    const messageIndex = thread.messages.findIndex(m => m.id === messageId);
    console.log('[StorageService] Message index:', messageIndex, 'out of', thread.messages.length, 'messages');
    if (messageIndex >= 0) {
      thread.messages[messageIndex] = { ...thread.messages[messageIndex], ...updates };
      this.saveThread(thread);
    } else {
      console.warn('[StorageService] Message not found:', messageId);
    }
  }

  /**
   * Clear all threads (useful for testing/debugging)
   */
  static clearAll(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(STORAGE_KEY);
  }

  /**
   * Update artifact_id for a thread
   */
  static updateThreadArtifactId(threadId: string, artifactId: string): void {
    console.log('[StorageService] updateThreadArtifactId:', threadId, artifactId);
    const thread = this.getThread(threadId);
    if (!thread) {
      console.error('[StorageService] Thread not found for artifact_id update:', threadId);
      return;
    }
    
    thread.artifactId = artifactId;
    this.saveThread(thread);
    console.log('[StorageService] Artifact ID saved to thread');
  }
}
