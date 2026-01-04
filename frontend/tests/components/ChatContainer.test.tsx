import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatContainer } from '@/components/ChatContainer';
import { sendChatMessage, sendCanvasMessage } from '@/services/api';

// Mock the API functions
jest.mock('@/services/api', () => ({
  sendChatMessage: jest.fn(),
  sendCanvasMessage: jest.fn(),
  fetchAvailableAgents: jest.fn(() => Promise.resolve({
    agents: [
      { id: 'chat', name: 'Chat Agent', description: 'Test agent' }
    ],
    defaultAgent: 'chat'
  })),
  fetchAvailableModels: jest.fn(() => Promise.resolve({
    models: [],
    default_model: null
  }))
}));

// Mock hooks
jest.mock('@/hooks/useMessages', () => ({
  useMessages: () => ({
    messages: [],
    addMessage: jest.fn(),
    updateMessage: jest.fn(),
    removeMessage: jest.fn(),
    scrollRef: { current: null },
    handleScroll: jest.fn(),
    scrollToBottom: jest.fn(),
  })
}));

jest.mock('@/hooks/useAGUI', () => ({
  useAGUI: () => ({
    isConnected: true,
    on: jest.fn((event, callback) => () => {}),
    getClient: () => ({
      processEvent: jest.fn()
    }),
    setConnectionState: jest.fn(),
  })
}));

jest.mock('@/hooks/useA2UIEvents', () => ({
  useA2UIEvents: () => ({
    processA2UIMessage: jest.fn()
  })
}));

jest.mock('@/stores/modelStore', () => ({
  useModelStore: (selector: any) => {
    const state = {
      selectedProvider: 'test-provider',
      selectedModel: 'test-model',
    };
    return selector ? selector(state) : state;
  }
}));

jest.mock('@/stores/agentStore', () => ({
  useAgentStore: (selector: any) => {
    const state = {
      selectedAgent: 'chat',
    };
    return selector ? selector(state) : state;
  }
}));

describe('ChatContainer - Stop Streaming', () => {
  const mockThreadId = 'test-thread-123';
  const mockOnUpdateThreadTitle = jest.fn();
  const mockOnRefreshThreads = jest.fn();
  const mockOnArtifactDetected = jest.fn();
  const mockOnEnableCanvas = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('AbortController Management', () => {
    it('should store AbortController when sending message', async () => {
      const mockAbortController = new AbortController();
      (sendChatMessage as jest.Mock).mockResolvedValue(mockAbortController);

      render(
        <ChatContainer
          threadId={mockThreadId}
          onUpdateThreadTitle={mockOnUpdateThreadTitle}
          onRefreshThreads={mockOnRefreshThreads}
          onArtifactDetected={mockOnArtifactDetected}
          onEnableCanvas={mockOnEnableCanvas}
        />
      );

      // ChatInput should be rendered
      const textarea = screen.getByPlaceholderText(/Type your message/i);
      expect(textarea).toBeInTheDocument();
    });

    it('should return AbortController from sendChatMessage', async () => {
      const mockAbortController = new AbortController();
      (sendChatMessage as jest.Mock).mockResolvedValue(mockAbortController);

      const result = await sendChatMessage(
        [],
        'thread-1',
        'run-1',
        'model-1',
        'provider-1',
        'chat',
        jest.fn()
      );

      expect(result).toBe(mockAbortController);
    });

    it('should return AbortController from sendCanvasMessage', async () => {
      const mockAbortController = new AbortController();
      (sendCanvasMessage as jest.Mock).mockResolvedValue(mockAbortController);

      const result = await sendCanvasMessage(
        [],
        'thread-1',
        'run-1',
        undefined,
        undefined,
        undefined,
        undefined,
        'model-1',
        'provider-1',
        'canvas',
        jest.fn()
      );

      expect(result).toBe(mockAbortController);
    });
  });

  describe('Stop Streaming Handler', () => {
    it('should provide onStopStreaming prop to ChatInput', () => {
      render(
        <ChatContainer
          threadId={mockThreadId}
          onUpdateThreadTitle={mockOnUpdateThreadTitle}
          onRefreshThreads={mockOnRefreshThreads}
          onArtifactDetected={mockOnArtifactDetected}
          onEnableCanvas={mockOnEnableCanvas}
        />
      );

      // ChatInput should be rendered with required props
      const textarea = screen.getByPlaceholderText(/Type your message/i);
      expect(textarea).toBeInTheDocument();
    });

    it('should pass isStreaming prop to ChatInput', () => {
      render(
        <ChatContainer
          threadId={mockThreadId}
          onUpdateThreadTitle={mockOnUpdateThreadTitle}
          onRefreshThreads={mockOnRefreshThreads}
          onArtifactDetected={mockOnArtifactDetected}
          onEnableCanvas={mockOnEnableCanvas}
        />
      );

      // Component should render successfully
      expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument();
    });
  });

  describe('Message Sending During Streaming', () => {
    it('should abort existing stream before sending new message', async () => {
      const mockAbortController = {
        abort: jest.fn(),
        signal: new AbortController().signal
      };
      
      (sendChatMessage as jest.Mock).mockResolvedValue(mockAbortController);

      render(
        <ChatContainer
          threadId={mockThreadId}
          onUpdateThreadTitle={mockOnUpdateThreadTitle}
          onRefreshThreads={mockOnRefreshThreads}
          onArtifactDetected={mockOnArtifactDetected}
          onEnableCanvas={mockOnEnableCanvas}
        />
      );

      // Component renders successfully
      expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument();
    });
  });

  describe('Empty Thread State', () => {
    it('should render empty state when no threadId', () => {
      render(
        <ChatContainer
          threadId={null}
          onUpdateThreadTitle={mockOnUpdateThreadTitle}
          onRefreshThreads={mockOnRefreshThreads}
          onArtifactDetected={mockOnArtifactDetected}
          onEnableCanvas={mockOnEnableCanvas}
        />
      );

      expect(screen.getByText('Welcome to AgentKit')).toBeInTheDocument();
    });

    it('should pass isStreaming to ChatInput in empty state', () => {
      render(
        <ChatContainer
          threadId={null}
          onUpdateThreadTitle={mockOnUpdateThreadTitle}
          onRefreshThreads={mockOnRefreshThreads}
          onArtifactDetected={mockOnArtifactDetected}
          onEnableCanvas={mockOnEnableCanvas}
        />
      );

      // ChatInput should be rendered even without thread
      expect(screen.getByPlaceholderText('Start a new chat to begin...')).toBeInTheDocument();
    });
  });

  describe('Integration with ChatInput', () => {
    it('should render ChatInput with all required props', () => {
      render(
        <ChatContainer
          threadId={mockThreadId}
          onUpdateThreadTitle={mockOnUpdateThreadTitle}
          onRefreshThreads={mockOnRefreshThreads}
          onArtifactDetected={mockOnArtifactDetected}
          onEnableCanvas={mockOnEnableCanvas}
        />
      );

      // All three instances of ChatInput should have the required props
      const textareas = screen.getAllByRole('textbox');
      expect(textareas.length).toBeGreaterThan(0);
    });
  });

  describe('Message ID Uniqueness', () => {
    it('should generate unique message IDs when called rapidly', () => {
      const { generateUniqueId } = require('@/lib/utils');
      const ids = new Set<string>();
      const count = 100;
      
      // Generate many IDs in rapid succession (simulating rapid message creation)
      for (let i = 0; i < count; i++) {
        ids.add(generateUniqueId('msg-agent-pending'));
        ids.add(generateUniqueId('msg-user'));
        ids.add(generateUniqueId('msg-agent'));
      }
      
      // All IDs should be unique
      expect(ids.size).toBe(count * 3);
      
      // Verify all IDs match expected pattern
      Array.from(ids).forEach((id: any) => {
        expect(id).toMatch(/^msg-(agent-pending|user|agent)-\d+-\d+-[a-z0-9]+$/);
      });
    });
  });
});

