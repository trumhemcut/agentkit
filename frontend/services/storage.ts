import { Thread, Message } from '@/types/chat';

const STORAGE_KEY = 'agentkit_threads';

/**
 * LocalStorage service for chat thread persistence
 */
export class StorageService {
  /**
   * Get all threads from localStorage
   */
  static getThreads(): Thread[] {
    if (typeof window === 'undefined') return [];
    
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
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
    return threads.find(t => t.id === threadId) || null;
  }

  /**
   * Save a thread (create or update)
   */
  static saveThread(thread: Thread): void {
    if (typeof window === 'undefined') return;
    
    try {
      const threads = this.getThreads();
      const existingIndex = threads.findIndex(t => t.id === thread.id);
      
      if (existingIndex >= 0) {
        threads[existingIndex] = { ...thread, updatedAt: Date.now() };
      } else {
        threads.push(thread);
      }
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
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
    const thread = this.getThread(threadId);
    if (!thread) return;
    
    thread.messages.push(message);
    this.saveThread(thread);
  }

  /**
   * Update a message in a thread
   */
  static updateMessage(threadId: string, messageId: string, updates: Partial<Message>): void {
    const thread = this.getThread(threadId);
    if (!thread) return;
    
    const messageIndex = thread.messages.findIndex(m => m.id === messageId);
    if (messageIndex >= 0) {
      thread.messages[messageIndex] = { ...thread.messages[messageIndex], ...updates };
      this.saveThread(thread);
    }
  }

  /**
   * Clear all threads (useful for testing/debugging)
   */
  static clearAll(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(STORAGE_KEY);
  }
}
