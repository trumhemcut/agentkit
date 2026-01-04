/**
 * Tests for message store
 */

import { useMessageStore } from '@/stores/messageStore';
import { Message } from '@/types/chat';

// Mock the API
jest.mock('@/services/api', () => ({
  messagesApi: {
    list: jest.fn(() => Promise.resolve({ messages: [] })),
    create: jest.fn((threadId, msg) => Promise.resolve({
      id: 'backend-id',
      thread_id: threadId,
      role: msg.role,
      content: msg.content,
      created_at: new Date().toISOString(),
    })),
  },
}));

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
  },
}));

describe('messageStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useMessageStore.setState({
      messagesByThread: {},
      isLoadingMessages: {},
    });
  });

  describe('addMessage', () => {
    it('should add a message to the store', async () => {
      const threadId = 'thread-1';
      const message: Message = {
        id: 'msg-1',
        threadId,
        role: 'user',
        content: 'Hello',
        timestamp: Date.now(),
      };

      await useMessageStore.getState().addMessage(threadId, message);

      const messages = useMessageStore.getState().messagesByThread[threadId];
      expect(messages).toHaveLength(1);
      expect(messages[0]).toEqual(message);
    });

    it('should prevent duplicate messages with the same ID', async () => {
      const threadId = 'thread-1';
      const message: Message = {
        id: 'msg-duplicate',
        threadId,
        role: 'user',
        content: 'Hello',
        timestamp: Date.now(),
      };

      // Add message twice
      await useMessageStore.getState().addMessage(threadId, message);
      await useMessageStore.getState().addMessage(threadId, message);

      const messages = useMessageStore.getState().messagesByThread[threadId];
      expect(messages).toHaveLength(1);
      expect(messages[0].id).toBe('msg-duplicate');
    });

    it('should prevent duplicate pending messages', async () => {
      const threadId = 'thread-1';
      const pendingMessage: Message = {
        id: 'msg-agent-pending-123',
        threadId,
        role: 'agent',
        content: '',
        timestamp: Date.now(),
        isPending: true,
        isStreaming: false,
      };

      // Simulate rapid calls that might create duplicates
      await Promise.all([
        useMessageStore.getState().addMessage(threadId, pendingMessage),
        useMessageStore.getState().addMessage(threadId, pendingMessage),
        useMessageStore.getState().addMessage(threadId, pendingMessage),
      ]);

      const messages = useMessageStore.getState().messagesByThread[threadId];
      expect(messages).toHaveLength(1);
      expect(messages[0].id).toBe('msg-agent-pending-123');
    });

    it('should prevent duplicate backend sync for the same message', async () => {
      const mockCreate = require('@/services/api').messagesApi.create;
      mockCreate.mockClear();
      
      const threadId = 'thread-1';
      const userMessage: Message = {
        id: 'msg-user-sync-test',
        threadId,
        role: 'user',
        content: 'Test sync',
        timestamp: Date.now(),
      };

      // Add message first time - should sync to backend
      await useMessageStore.getState().addMessage(threadId, userMessage);
      expect(mockCreate).toHaveBeenCalledTimes(1);

      // Try to add same message again - should NOT sync to backend
      await useMessageStore.getState().addMessage(threadId, userMessage);
      expect(mockCreate).toHaveBeenCalledTimes(1); // Still 1, not 2

      const messages = useMessageStore.getState().messagesByThread[threadId];
      expect(messages).toHaveLength(1);
    });

    it('should allow multiple messages with different IDs', async () => {
      const threadId = 'thread-1';
      const message1: Message = {
        id: 'msg-1',
        threadId,
        role: 'user',
        content: 'Hello',
        timestamp: Date.now(),
      };
      const message2: Message = {
        id: 'msg-2',
        threadId,
        role: 'agent',
        content: 'Hi',
        timestamp: Date.now(),
      };

      await useMessageStore.getState().addMessage(threadId, message1);
      await useMessageStore.getState().addMessage(threadId, message2);

      const messages = useMessageStore.getState().messagesByThread[threadId];
      expect(messages).toHaveLength(2);
      expect(messages[0].id).toBe('msg-1');
      expect(messages[1].id).toBe('msg-2');
    });

    it('should handle rapid message additions without duplicates', async () => {
      const threadId = 'thread-1';
      const messages: Message[] = [];

      // Create 10 unique messages
      for (let i = 0; i < 10; i++) {
        messages.push({
          id: `msg-${i}`,
          threadId,
          role: i % 2 === 0 ? 'user' : 'agent',
          content: `Message ${i}`,
          timestamp: Date.now() + i,
        });
      }

      // Add all messages rapidly
      await Promise.all(
        messages.map(msg => useMessageStore.getState().addMessage(threadId, msg))
      );

      const storedMessages = useMessageStore.getState().messagesByThread[threadId];
      expect(storedMessages).toHaveLength(10);

      // Verify all IDs are unique
      const ids = storedMessages.map(m => m.id);
      const uniqueIds = [...new Set(ids)];
      expect(ids.length).toBe(uniqueIds.length);
    });
  });

  describe('updateMessage', () => {
    it('should update message content', () => {
      const threadId = 'thread-1';
      const message: Message = {
        id: 'msg-1',
        threadId,
        role: 'agent',
        content: 'Initial',
        timestamp: Date.now(),
      };

      // Add message
      useMessageStore.getState().addMessage(threadId, message);

      // Update content
      useMessageStore.getState().updateMessage(threadId, 'msg-1', {
        content: 'Updated content',
      });

      const messages = useMessageStore.getState().messagesByThread[threadId];
      expect(messages[0].content).toBe('Updated content');
    });

    it('should not create duplicates when updating', () => {
      const threadId = 'thread-1';
      const message: Message = {
        id: 'msg-1',
        threadId,
        role: 'agent',
        content: 'Initial',
        timestamp: Date.now(),
      };

      useMessageStore.getState().addMessage(threadId, message);

      // Update multiple times
      useMessageStore.getState().updateMessage(threadId, 'msg-1', { content: 'V1' });
      useMessageStore.getState().updateMessage(threadId, 'msg-1', { content: 'V2' });
      useMessageStore.getState().updateMessage(threadId, 'msg-1', { content: 'V3' });

      const messages = useMessageStore.getState().messagesByThread[threadId];
      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe('V3');
    });
  });
});
