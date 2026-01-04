/**
 * Tests for database persistence API client
 * 
 * Tests threadsApi and messagesApi with mocked fetch calls
 */

import { threadsApi, messagesApi } from '@/services/api';

// Mock fetch globally
global.fetch = jest.fn();

describe('threadsApi', () => {
  const mockThread = {
    id: 'thread-123',
    title: 'Test Thread',
    agent_id: 'chat',
    model: 'qwen:7b',
    provider: 'ollama',
    created_at: '2026-01-04T00:00:00.000Z',
    updated_at: '2026-01-04T00:00:00.000Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('create', () => {
    it('should create a thread with valid data', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockThread,
      });

      const result = await threadsApi.create({
        agent_id: 'chat',
        model: 'qwen:7b',
        provider: 'ollama',
        title: 'Test Thread',
      });

      expect(result).toEqual(mockThread);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id: 'chat',
            model: 'qwen:7b',
            provider: 'ollama',
            title: 'Test Thread',
          }),
        })
      );
    });

    it('should throw error on failed request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      });

      await expect(
        threadsApi.create({
          agent_id: 'chat',
          model: 'qwen:7b',
          provider: 'ollama',
        })
      ).rejects.toThrow('Failed to create thread: Bad Request');
    });
  });

  describe('list', () => {
    it('should list threads with pagination', async () => {
      const mockResponse = {
        threads: [mockThread],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await threadsApi.list(10, 0);

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads?limit=10&offset=0')
      );
    });

    it('should use default pagination values', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ threads: [] }),
      });

      await threadsApi.list();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads?limit=50&offset=0')
      );
    });
  });

  describe('get', () => {
    it('should get a thread by ID', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockThread,
      });

      const result = await threadsApi.get('thread-123');

      expect(result).toEqual(mockThread);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads/thread-123')
      );
    });

    it('should throw error when thread not found', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(threadsApi.get('invalid-id')).rejects.toThrow(
        'Failed to get thread: Not Found'
      );
    });
  });

  describe('update', () => {
    it('should update thread title', async () => {
      const updatedThread = { ...mockThread, title: 'Updated Title' };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => updatedThread,
      });

      const result = await threadsApi.update('thread-123', { title: 'Updated Title' });

      expect(result).toEqual(updatedThread);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads/thread-123'),
        expect.objectContaining({
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: 'Updated Title' }),
        })
      );
    });
  });

  describe('delete', () => {
    it('should delete a thread', async () => {
      const mockResponse = { message: 'Thread deleted successfully' };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await threadsApi.delete('thread-123');

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads/thread-123'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });
});

describe('messagesApi', () => {
  const mockMessage = {
    id: 'message-123',
    thread_id: 'thread-123',
    role: 'user' as const,
    content: 'Hello, world!',
    artifact_data: null,
    metadata: null,
    created_at: '2026-01-04T00:00:00.000Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('create', () => {
    it('should create a message with text content', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMessage,
      });

      const result = await messagesApi.create('thread-123', {
        role: 'user',
        content: 'Hello, world!',
      });

      expect(result).toEqual(mockMessage);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads/thread-123/messages'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            role: 'user',
            content: 'Hello, world!',
          }),
        })
      );
    });

    it('should create a message with artifact data', async () => {
      const messageWithArtifact = {
        ...mockMessage,
        artifact_data: {
          type: 'code',
          language: 'python',
          title: 'Test Code',
        },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => messageWithArtifact,
      });

      const result = await messagesApi.create('thread-123', {
        role: 'assistant',
        content: 'Here is some code',
        artifact_data: {
          type: 'code',
          language: 'python',
          title: 'Test Code',
        },
      });

      expect(result.artifact_data).toBeTruthy();
    });

    it('should throw error on failed request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      });

      await expect(
        messagesApi.create('thread-123', {
          role: 'user',
          content: 'Test',
        })
      ).rejects.toThrow('Failed to create message: Bad Request');
    });
  });

  describe('list', () => {
    it('should list messages in a thread', async () => {
      const mockResponse = {
        messages: [mockMessage],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await messagesApi.list('thread-123');

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/threads/thread-123/messages')
      );
    });

    it('should handle empty message list', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ messages: [] }),
      });

      const result = await messagesApi.list('thread-123');

      expect(result.messages).toEqual([]);
    });
  });

  describe('delete', () => {
    it('should delete a message', async () => {
      const mockResponse = { message: 'Message deleted successfully' };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await messagesApi.delete('message-123');

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/messages/message-123'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('should throw error when message not found', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(messagesApi.delete('invalid-id')).rejects.toThrow(
        'Failed to delete message: Not Found'
      );
    });
  });
});
