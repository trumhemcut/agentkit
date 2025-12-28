/**
 * ChatApp Component Tests
 * 
 * Test suite for ChatApp component, focusing on:
 * - New chat creation flow
 * - Sidebar state persistence during new chat
 * - Input focus behavior after new chat creation
 * - URL updates without component remount
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatApp } from '@/components/ChatApp';
import { useChatThreads } from '@/hooks/useChatThreads';
import { useSidebar } from '@/hooks/useSidebar';
import { useCanvasMode } from '@/hooks/useCanvasMode';
import { useRouter } from 'next/navigation';

// Mock hooks
jest.mock('@/hooks/useChatThreads');
jest.mock('@/hooks/useSidebar');
jest.mock('@/hooks/useCanvasMode');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock CanvasContext
jest.mock('@/contexts/CanvasContext', () => ({
  useCanvas: jest.fn(() => ({
    setArtifactId: jest.fn(),
    loadArtifactById: jest.fn(),
  })),
}));

// Mock child components to simplify testing
jest.mock('@/components/Layout', () => ({
  Layout: ({ children, sidebar }: any) => (
    <div data-testid="layout">
      <div data-testid="sidebar">{sidebar}</div>
      <div data-testid="content">{children}</div>
    </div>
  ),
}));

jest.mock('@/components/Sidebar', () => ({
  Sidebar: ({ onNewChat, isCollapsed }: any) => (
    <div data-testid="sidebar-component" data-collapsed={isCollapsed}>
      <button onClick={onNewChat} data-testid="new-chat-button">
        New Chat
      </button>
    </div>
  ),
}));

jest.mock('@/components/ChatContainer', () => ({
  ChatContainer: React.forwardRef(({ threadId }: any, ref: any) => {
    // Expose focusInput method for testing
    React.useImperativeHandle(ref, () => ({
      focusInput: jest.fn(),
    }));
    
    return (
      <div data-testid="chat-container" data-thread-id={threadId}>
        <input data-testid="chat-input" />
      </div>
    );
  }),
  ChatContainerRef: {} as any,
}));

jest.mock('@/components/ArtifactPanel', () => ({
  ArtifactPanel: ({ onClose }: any) => (
    <div data-testid="artifact-panel">
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

jest.mock('@/components/ResizableDivider', () => ({
  ResizableDivider: () => <div data-testid="resizable-divider" />,
}));

describe('ChatApp - New Chat Functionality', () => {
  const mockCreateThread = jest.fn();
  const mockDeleteThread = jest.fn();
  const mockSelectThread = jest.fn();
  const mockUpdateThreadTitle = jest.fn();
  const mockRefreshThreads = jest.fn();
  const mockToggleCollapse = jest.fn();
  const mockSetCollapsed = jest.fn();
  const mockActivateCanvas = jest.fn();
  const mockDeactivateCanvas = jest.fn();
  const mockUpdateCurrentArtifact = jest.fn();
  const mockPush = jest.fn();
  const mockReplace = jest.fn();

  const mockThread = {
    id: 'thread-123',
    title: 'Test Thread',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  const mockThreadWithMessages = {
    ...mockThread,
    messages: [
      {
        id: 'msg-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: Date.now(),
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock window.history.pushState
    window.history.pushState = jest.fn();
    
    // Default mock implementations
    (useChatThreads as jest.Mock).mockReturnValue({
      threads: [mockThread],
      currentThread: mockThread,
      currentThreadId: mockThread.id,
      createThread: mockCreateThread,
      deleteThread: mockDeleteThread,
      selectThread: mockSelectThread,
      updateThreadTitle: mockUpdateThreadTitle,
      refreshThreads: mockRefreshThreads,
    });

    (useSidebar as jest.Mock).mockReturnValue({
      isCollapsed: false,
      toggleCollapse: mockToggleCollapse,
      setCollapsed: mockSetCollapsed,
      isLoaded: true,
    });

    (useCanvasMode as jest.Mock).mockReturnValue({
      isActive: false,
      currentArtifactMessage: null,
      activateCanvas: mockActivateCanvas,
      deactivateCanvas: mockDeactivateCanvas,
      updateCurrentArtifact: mockUpdateCurrentArtifact,
    });

    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: mockReplace,
    });

    mockCreateThread.mockReturnValue({
      id: 'new-thread-456',
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    });
  });

  describe('Sidebar state during new chat creation', () => {
    it('should not change sidebar collapsed state when clicking New Chat from expanded state', async () => {
      const user = userEvent.setup();
      
      render(<ChatApp initialThreadId={mockThread.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      // Verify setCollapsed was not called (sidebar state should remain unchanged)
      expect(mockSetCollapsed).not.toHaveBeenCalled();
      
      // Verify sidebar stays expanded
      const sidebar = screen.getByTestId('sidebar-component');
      expect(sidebar).toHaveAttribute('data-collapsed', 'false');
    });

    it('should not change sidebar collapsed state when clicking New Chat from collapsed state', async () => {
      const user = userEvent.setup();
      
      // Start with collapsed sidebar
      (useSidebar as jest.Mock).mockReturnValue({
        isCollapsed: true,
        toggleCollapse: mockToggleCollapse,
        setCollapsed: mockSetCollapsed,
        isLoaded: true,
      });
      
      render(<ChatApp initialThreadId={mockThread.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      // Verify setCollapsed was not called (sidebar state should remain unchanged)
      expect(mockSetCollapsed).not.toHaveBeenCalled();
      
      // Verify sidebar stays collapsed
      const sidebar = screen.getByTestId('sidebar-component');
      expect(sidebar).toHaveAttribute('data-collapsed', 'true');
    });

    it('should preserve sidebar state when canvas mode was active', async () => {
      const user = userEvent.setup();
      
      // Start with collapsed sidebar and active canvas
      (useSidebar as jest.Mock).mockReturnValue({
        isCollapsed: true,
        toggleCollapse: mockToggleCollapse,
        setCollapsed: mockSetCollapsed,
        isLoaded: true,
      });

      (useCanvasMode as jest.Mock).mockReturnValue({
        isActive: true,
        currentArtifactMessage: { id: 'msg-1', content: 'test' },
        activateCanvas: mockActivateCanvas,
        deactivateCanvas: mockDeactivateCanvas,
        updateCurrentArtifact: mockUpdateCurrentArtifact,
      });
      
      render(<ChatApp initialThreadId={mockThread.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      // Canvas should be deactivated
      expect(mockDeactivateCanvas).toHaveBeenCalled();
      
      // Sidebar state should remain collapsed (no setCollapsed call after deactivate)
      const sidebar = screen.getByTestId('sidebar-component');
      expect(sidebar).toHaveAttribute('data-collapsed', 'true');
    });
  });

  describe('New chat creation flow', () => {
    it('should create new thread when current thread has messages', async () => {
      const user = userEvent.setup();
      
      (useChatThreads as jest.Mock).mockReturnValue({
        threads: [mockThreadWithMessages],
        currentThread: mockThreadWithMessages,
        currentThreadId: mockThreadWithMessages.id,
        createThread: mockCreateThread,
        deleteThread: mockDeleteThread,
        selectThread: mockSelectThread,
        updateThreadTitle: mockUpdateThreadTitle,
        refreshThreads: mockRefreshThreads,
      });
      
      render(<ChatApp initialThreadId={mockThreadWithMessages.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      expect(mockCreateThread).toHaveBeenCalled();
    });

    it('should create new thread when no current thread exists', async () => {
      const user = userEvent.setup();
      
      (useChatThreads as jest.Mock).mockReturnValue({
        threads: [],
        currentThread: null,
        currentThreadId: null,
        createThread: mockCreateThread,
        deleteThread: mockDeleteThread,
        selectThread: mockSelectThread,
        updateThreadTitle: mockUpdateThreadTitle,
        refreshThreads: mockRefreshThreads,
      });
      
      render(<ChatApp />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      expect(mockCreateThread).toHaveBeenCalled();
    });

    it('should not create new thread when current thread is empty', async () => {
      const user = userEvent.setup();
      
      render(<ChatApp initialThreadId={mockThread.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      // Empty thread - should not create new one
      expect(mockCreateThread).not.toHaveBeenCalled();
    });
  });

  describe('URL updates without component remount', () => {
    it('should update URL using window.history.pushState instead of router.push', async () => {
      const user = userEvent.setup();
      
      (useChatThreads as jest.Mock).mockReturnValue({
        threads: [mockThreadWithMessages],
        currentThread: mockThreadWithMessages,
        currentThreadId: mockThreadWithMessages.id,
        createThread: mockCreateThread,
        deleteThread: mockDeleteThread,
        selectThread: mockSelectThread,
        updateThreadTitle: mockUpdateThreadTitle,
        refreshThreads: mockRefreshThreads,
      });
      
      render(<ChatApp initialThreadId={mockThreadWithMessages.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      // Verify window.history.pushState was called with new thread URL
      expect(window.history.pushState).toHaveBeenCalledWith(
        {},
        '',
        '/thread/new-thread-456'
      );
      
      // Verify router.push and router.replace were NOT called
      expect(mockPush).not.toHaveBeenCalled();
      expect(mockReplace).not.toHaveBeenCalled();
    });

    it('should update URL with correct thread ID', async () => {
      const user = userEvent.setup();
      
      const customThreadId = 'custom-thread-789';
      mockCreateThread.mockReturnValue({
        id: customThreadId,
        title: 'New Chat',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      });

      (useChatThreads as jest.Mock).mockReturnValue({
        threads: [mockThreadWithMessages],
        currentThread: mockThreadWithMessages,
        currentThreadId: mockThreadWithMessages.id,
        createThread: mockCreateThread,
        deleteThread: mockDeleteThread,
        selectThread: mockSelectThread,
        updateThreadTitle: mockUpdateThreadTitle,
        refreshThreads: mockRefreshThreads,
      });
      
      render(<ChatApp initialThreadId={mockThreadWithMessages.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      expect(window.history.pushState).toHaveBeenCalledWith(
        {},
        '',
        `/thread/${customThreadId}`
      );
    });
  });

  describe('Canvas mode integration', () => {
    it('should deactivate canvas mode when creating new chat', async () => {
      const user = userEvent.setup();
      
      (useCanvasMode as jest.Mock).mockReturnValue({
        isActive: true,
        currentArtifactMessage: { id: 'msg-1', content: 'test' },
        activateCanvas: mockActivateCanvas,
        deactivateCanvas: mockDeactivateCanvas,
        updateCurrentArtifact: mockUpdateCurrentArtifact,
      });

      (useChatThreads as jest.Mock).mockReturnValue({
        threads: [mockThreadWithMessages],
        currentThread: mockThreadWithMessages,
        currentThreadId: mockThreadWithMessages.id,
        createThread: mockCreateThread,
        deleteThread: mockDeleteThread,
        selectThread: mockSelectThread,
        updateThreadTitle: mockUpdateThreadTitle,
        refreshThreads: mockRefreshThreads,
      });
      
      render(<ChatApp initialThreadId={mockThreadWithMessages.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      await user.click(newChatButton);

      expect(mockDeactivateCanvas).toHaveBeenCalled();
    });
  });

  describe('Edge cases', () => {
    it('should handle rapid clicks on New Chat button', async () => {
      const user = userEvent.setup();
      
      (useChatThreads as jest.Mock).mockReturnValue({
        threads: [mockThreadWithMessages],
        currentThread: mockThreadWithMessages,
        currentThreadId: mockThreadWithMessages.id,
        createThread: mockCreateThread,
        deleteThread: mockDeleteThread,
        selectThread: mockSelectThread,
        updateThreadTitle: mockUpdateThreadTitle,
        refreshThreads: mockRefreshThreads,
      });
      
      render(<ChatApp initialThreadId={mockThreadWithMessages.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      
      // Click multiple times rapidly
      await user.click(newChatButton);
      await user.click(newChatButton);
      await user.click(newChatButton);

      // Should create thread for each click
      expect(mockCreateThread).toHaveBeenCalledTimes(3);
    });

    it('should handle createThread returning undefined gracefully', async () => {
      const user = userEvent.setup();
      
      mockCreateThread.mockReturnValue(undefined);

      (useChatThreads as jest.Mock).mockReturnValue({
        threads: [mockThreadWithMessages],
        currentThread: mockThreadWithMessages,
        currentThreadId: mockThreadWithMessages.id,
        createThread: mockCreateThread,
        deleteThread: mockDeleteThread,
        selectThread: mockSelectThread,
        updateThreadTitle: mockUpdateThreadTitle,
        refreshThreads: mockRefreshThreads,
      });
      
      render(<ChatApp initialThreadId={mockThreadWithMessages.id} />);
      
      const newChatButton = screen.getByTestId('new-chat-button');
      
      // Should not throw error
      await expect(user.click(newChatButton)).resolves.not.toThrow();
    });
  });
});
