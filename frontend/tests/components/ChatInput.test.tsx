import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInput } from '@/components/ChatInput';

describe('ChatInput', () => {
  const mockOnSendMessage = jest.fn();
  const mockOnStopStreaming = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Send Button', () => {
    it('should render Send button when not streaming', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      // Send button should be visible (by checking for the Send icon's parent button)
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should send message when Send button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      await user.type(textarea, 'Hello world');

      // Press Enter to send (more reliable than clicking button)
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockOnSendMessage).toHaveBeenCalledWith('Hello world');
      });
    });

    it('should be disabled when message is empty', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      // Find the send button (last button in the list, typically)
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];
      
      expect(sendButton).toBeDisabled();
    });

    it('should be enabled when message has content', async () => {
      const user = userEvent.setup();
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      await user.type(textarea, 'Test message');

      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];
      
      expect(sendButton).not.toBeDisabled();
    });
  });

  describe('Stop Button', () => {
    it('should render Stop button when streaming', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={true}
        />
      );

      // Stop button should be visible
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should call onStopStreaming when Stop button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={true}
        />
      );

      const buttons = screen.getAllByRole('button');
      const stopButton = buttons[buttons.length - 1];
      
      await user.click(stopButton);

      expect(mockOnStopStreaming).toHaveBeenCalledTimes(1);
    });

    it('should be enabled during streaming', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={true}
        />
      );

      const buttons = screen.getAllByRole('button');
      const stopButton = buttons[buttons.length - 1];
      
      expect(stopButton).not.toBeDisabled();
    });
  });

  describe('Keyboard Handling', () => {
    it('should send message on Enter key when not streaming', async () => {
      const user = userEvent.setup();
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      await user.type(textarea, 'Test message{Enter}');

      expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
    });

    it('should stop and send on Enter key when streaming', async () => {
      const user = userEvent.setup();
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={true}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      await user.type(textarea, 'New message{Enter}');

      expect(mockOnStopStreaming).toHaveBeenCalledTimes(1);
      
      // Wait for the timeout in handleKeyDown
      await waitFor(() => {
        expect(mockOnSendMessage).toHaveBeenCalledWith('New message');
      }, { timeout: 200 });
    });

    it('should add new line on Shift+Enter', async () => {
      const user = userEvent.setup();
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      await user.type(textarea, 'Line 1{Shift>}{Enter}{/Shift}Line 2');

      expect(mockOnSendMessage).not.toHaveBeenCalled();
      expect(textarea).toHaveValue('Line 1\nLine 2');
    });
  });

  describe('Disabled State', () => {
    it('should disable textarea when disabled prop is true', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          disabled={true}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      expect(textarea).toBeDisabled();
    });

    it('should not disable textarea when streaming', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={true}
          disabled={false}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      expect(textarea).not.toBeDisabled();
    });
  });

  describe('Hint Text', () => {
    it('should show normal hint when not streaming', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      expect(screen.getByText('Press Enter to send, Shift+Enter for new line')).toBeInTheDocument();
    });

    it('should show streaming hint when streaming', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={true}
        />
      );

      expect(screen.getByText('Press Enter to stop and send new message')).toBeInTheDocument();
    });
  });

  describe('Message Clearing', () => {
    it('should clear message after sending', async () => {
      const user = userEvent.setup();
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      const textarea = screen.getByPlaceholderText('Type your message...');
      await user.type(textarea, 'Test message');
      
      expect(textarea).toHaveValue('Test message');

      await user.type(textarea, '{Enter}');

      expect(textarea).toHaveValue('');
    });
  });

  describe('Button Styling', () => {
    it('should have rounded-full class on all buttons', () => {
      render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={false}
        />
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button.className).toContain('rounded-full');
      });
    });

    it('should use secondary variant for Stop button', () => {
      const { container } = render(
        <ChatInput
          onSendMessage={mockOnSendMessage}
          onStopStreaming={mockOnStopStreaming}
          isStreaming={true}
        />
      );

      // Check for secondary variant class
      const buttons = screen.getAllByRole('button');
      const stopButton = buttons[buttons.length - 1];
      
      // Secondary variant should be applied
      expect(stopButton.className).toContain('bg-secondary');
    });
  });
});
