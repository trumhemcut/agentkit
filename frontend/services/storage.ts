import { Thread, Message } from '@/types/chat';
import { Thread as ServerThread } from '@/types/database';
import { threadsApi, messagesApi } from './api';

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
   * Update message ID (replace temp frontend ID with backend ID)
   * Phase 1: Updates message ID in localStorage after backend sync
   */
  static updateMessageId(threadId: string, tempId: string, backendId: string): void {
    console.log('[StorageService] updateMessageId:', tempId, '→', backendId);
    const thread = this.getThread(threadId);
    if (!thread) {
      console.error('[StorageService] Thread not found for ID update:', threadId);
      return;
    }
    
    const messageIndex = thread.messages.findIndex(m => m.id === tempId);
    if (messageIndex >= 0) {
      thread.messages[messageIndex] = { ...thread.messages[messageIndex], id: backendId };
      this.saveThread(thread);
      console.log('[StorageService] Message ID updated in localStorage');
    } else {
      console.warn('[StorageService] Message with temp ID not found:', tempId);
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

  /**
   * Phase 1: Background sync to server
   * 
   * These methods persist data to the server in the background while
   * maintaining LocalStorage as the primary data source.
   */

  /**
   * Sync a thread to the server and get server-generated ID
   * Returns the server thread with authoritative ID
   * Throws error if sync fails to enable proper error handling
   */
  static async syncThreadToServer(thread: Thread, agentId: string, model: string, provider: string): Promise<ServerThread> {
    const serverThread = await threadsApi.create({
      agent_id: agentId,
      model: model,
      provider: provider,
      title: thread.title,
    });
    console.log('[StorageService] ✅ Thread created on server with ID:', serverThread.id);
    return serverThread;
  }

  /**
   * Sync a message to the server in the background
   * Returns the backend message with server-generated ID
   * Phase 1: Non-blocking operation that enables ID synchronization
   */
  static async syncMessageToServer(threadId: string, message: Message): Promise<{ id: string } | null> {
    // Skip sync for pending or streaming messages
    if (message.isPending || message.isStreaming) {
      console.log('[StorageService] ⏭️ Skipping sync for pending/streaming message:', message.id);
      return null;
    }

    // Skip sync for messages with empty content (unless they have artifacts)
    if (!message.content && !message.artifactType) {
      console.log('[StorageService] ⏭️ Skipping sync for empty message:', message.id);
      return null;
    }

    try {
      const backendMessage = await messagesApi.create(threadId, {
        role: message.role === 'agent' ? 'assistant' : message.role,
        content: message.content || undefined,
        artifact_data: message.artifactType ? {
          type: message.artifactType,
          language: message.language,
          title: message.title,
          artifactId: message.artifactId,
        } : undefined,
        metadata: message.metadata || undefined,
      });
      console.log('[StorageService] ✅ Message synced to server with ID:', backendMessage.id);
      return backendMessage;
    } catch (error) {
      console.error('[StorageService] ⚠️ Failed to sync message to server (non-blocking):', error);
      // Don't throw - this is a background operation
      return null;
    }
  }

  /**
   * Update thread title on server
   * Does not block or affect the UI if update fails
   */
  static async syncThreadTitleToServer(threadId: string, title: string): Promise<void> {
    try {
      await threadsApi.update(threadId, { title });
      console.log('[StorageService] ✅ Thread title synced to server:', threadId);
    } catch (error) {
      console.error('[StorageService] ⚠️ Failed to sync thread title to server (non-blocking):', error);
      // Don't throw - this is a background operation
    }
  }

  /**
   * Delete thread from server
   * Does not block or affect the UI if delete fails
   */
  static async syncThreadDeleteToServer(threadId: string): Promise<void> {
    try {
      await threadsApi.delete(threadId);
      console.log('[StorageService] ✅ Thread deletion synced to server:', threadId);
    } catch (error) {
      console.error('[StorageService] ⚠️ Failed to sync thread deletion to server (non-blocking):', error);
      // Don't throw - this is a background operation
    }
  }
}
