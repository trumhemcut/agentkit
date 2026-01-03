import { sendChatMessage, sendCanvasMessage } from '@/services/api';

// Mock fetch
global.fetch = jest.fn();

describe('API Service - AbortController', () => {
  const mockOnEvent = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  describe('sendChatMessage', () => {
    it('should return AbortController', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"type":"RUN_STARTED"}\n') })
          .mockResolvedValueOnce({ done: true, value: undefined })
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        body: {
          getReader: () => mockReader
        }
      });

      const result = await sendChatMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        'model-1',
        'provider-1',
        'chat',
        mockOnEvent
      );

      expect(result).toBeInstanceOf(AbortController);
    });

    it('should add abort signal to fetch request', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: true, value: undefined })
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        body: {
          getReader: () => mockReader
        }
      });

      await sendChatMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        'model-1',
        'provider-1',
        'chat',
        mockOnEvent
      );

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          signal: expect.any(AbortSignal)
        })
      );
    });

    it('should handle AbortError specifically', async () => {
      const abortError = new DOMException('The user aborted a request.', 'AbortError');
      (global.fetch as jest.Mock).mockRejectedValue(abortError);

      const result = await sendChatMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        'model-1',
        'provider-1',
        'chat',
        mockOnEvent
      );

      expect(mockOnEvent).toHaveBeenCalledWith({
        type: 'STREAM_ABORTED',
        message: 'Request cancelled by user',
        timestamp: expect.any(Number)
      });
      expect(result).toBeInstanceOf(AbortController);
    });

    it('should handle other errors', async () => {
      const error = new Error('Network error');
      (global.fetch as jest.Mock).mockRejectedValue(error);

      await sendChatMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        'model-1',
        'provider-1',
        'chat',
        mockOnEvent
      );

      expect(mockOnEvent).toHaveBeenCalledWith({
        type: 'ERROR',
        message: 'Network error',
        timestamp: expect.any(Number)
      });
    });

    it('should process streaming events correctly', async () => {
      const events = [
        'data: {"type":"RUN_STARTED","run_id":"run-1"}\n',
        'data: {"type":"TEXT_MESSAGE_START","message_id":"msg-1"}\n',
        'data: {"type":"TEXT_MESSAGE_CONTENT","content":"Hello"}\n',
        'data: {"type":"TEXT_MESSAGE_END"}\n',
        'data: {"type":"RUN_FINISHED"}\n'
      ];

      const mockReader = {
        read: jest.fn()
      };

      events.forEach((event, index) => {
        mockReader.read.mockResolvedValueOnce({
          done: false,
          value: new TextEncoder().encode(event)
        });
      });
      mockReader.read.mockResolvedValueOnce({ done: true, value: undefined });

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        body: {
          getReader: () => mockReader
        }
      });

      await sendChatMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        'model-1',
        'provider-1',
        'chat',
        mockOnEvent
      );

      expect(mockOnEvent).toHaveBeenCalledTimes(5);
      expect(mockOnEvent).toHaveBeenNthCalledWith(1, expect.objectContaining({ type: 'RUN_STARTED' }));
      expect(mockOnEvent).toHaveBeenNthCalledWith(2, expect.objectContaining({ type: 'TEXT_MESSAGE_START' }));
      expect(mockOnEvent).toHaveBeenNthCalledWith(3, expect.objectContaining({ type: 'TEXT_MESSAGE_CONTENT' }));
    });
  });

  describe('sendCanvasMessage', () => {
    it('should return AbortController', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: true, value: undefined })
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        body: {
          getReader: () => mockReader
        }
      });

      const result = await sendCanvasMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        undefined,
        undefined,
        undefined,
        undefined,
        'model-1',
        'provider-1',
        'canvas',
        mockOnEvent
      );

      expect(result).toBeInstanceOf(AbortController);
    });

    it('should add abort signal to fetch request', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: true, value: undefined })
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        body: {
          getReader: () => mockReader
        }
      });

      await sendCanvasMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        undefined,
        undefined,
        undefined,
        undefined,
        'model-1',
        'provider-1',
        'canvas',
        mockOnEvent
      );

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          signal: expect.any(AbortSignal)
        })
      );
    });

    it('should handle AbortError specifically', async () => {
      const abortError = new DOMException('The user aborted a request.', 'AbortError');
      (global.fetch as jest.Mock).mockRejectedValue(abortError);

      const result = await sendCanvasMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        undefined,
        undefined,
        undefined,
        undefined,
        'model-1',
        'provider-1',
        'canvas',
        mockOnEvent
      );

      expect(mockOnEvent).toHaveBeenCalledWith({
        type: 'STREAM_ABORTED',
        message: 'Request cancelled by user',
        timestamp: expect.any(Number)
      });
      expect(result).toBeInstanceOf(AbortController);
    });
  });

  describe('AbortController behavior', () => {
    it('should allow aborting an ongoing request', async () => {
      const abortController = new AbortController();
      
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"type":"TEXT_MESSAGE_CONTENT","content":"chunk"}\n') })
          .mockResolvedValueOnce({ done: true, value: undefined })
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        body: {
          getReader: () => mockReader
        }
      });

      const result = await sendChatMessage(
        [{ role: 'user', content: 'Hello' }],
        'thread-1',
        'run-1',
        'model-1',
        'provider-1',
        'chat',
        mockOnEvent
      );

      expect(result).toBeInstanceOf(AbortController);
      
      // Abort the request
      result.abort();
      
      expect(result.signal.aborted).toBe(true);
    });
  });
});
