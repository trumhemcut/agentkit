/**
 * MessageBubble Component Tests
 * 
 * Test suite to ensure MessageBubble components maintain correct height
 * and padding after Shadcn UI updates.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '@/components/MessageBubble';
import { UserMessageBubble } from '@/components/UserMessageBubble';
import { AgentMessageBubble } from '@/components/AgentMessageBubble';
import type { Message } from '@/types/chat';

describe('MessageBubble', () => {
  const mockUserMessage: Message = {
    id: '1',
    role: 'user',
    content: 'Hello, this is a user message',
    timestamp: Date.now(),
  };

  const mockAgentMessage: Message = {
    id: '2',
    role: 'assistant',
    content: 'Hello, this is an agent response',
    timestamp: Date.now(),
  };

  describe('UserMessageBubble', () => {
    it('renders user message with correct content', () => {
      render(<UserMessageBubble message={mockUserMessage} />);
      expect(screen.getByText(mockUserMessage.content)).toBeInTheDocument();
    });

    it('applies py-0 class to Card to override default Shadcn padding', () => {
      const { container } = render(<UserMessageBubble message={mockUserMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      expect(card).toHaveClass('py-0');
    });

    it('applies p-3 class to CardContent', () => {
      const { container } = render(<UserMessageBubble message={mockUserMessage} />);
      const cardContent = container.querySelector('[data-slot="card-content"]');
      expect(cardContent).toHaveClass('p-3');
    });

    it('has no extra vertical padding from Shadcn Card component', () => {
      const { container } = render(<UserMessageBubble message={mockUserMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      // Verify py-0 overrides the default py-6 from Shadcn Card
      expect(card).not.toHaveClass('py-6');
    });
  });

  describe('AgentMessageBubble', () => {
    it('renders agent message with correct content', () => {
      render(<AgentMessageBubble message={mockAgentMessage} />);
      expect(screen.getByText(mockAgentMessage.content)).toBeInTheDocument();
    });

    it('applies py-0 class to Card to override default Shadcn padding', () => {
      const { container } = render(<AgentMessageBubble message={mockAgentMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      expect(card).toHaveClass('py-0');
    });

    it('applies p-3 class to CardContent', () => {
      const { container } = render(<AgentMessageBubble message={mockAgentMessage} />);
      const cardContent = container.querySelector('[data-slot="card-content"]');
      expect(cardContent).toHaveClass('p-3');
    });

    it('has no extra vertical padding from Shadcn Card component', () => {
      const { container } = render(<AgentMessageBubble message={mockAgentMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      // Verify py-0 overrides the default py-6 from Shadcn Card
      expect(card).not.toHaveClass('py-6');
    });

    it('renders thinking state with Loader2 icon', () => {
      const thinkingMessage: Message = {
        ...mockAgentMessage,
        content: '',
        isPending: true,
      };
      render(<AgentMessageBubble message={thinkingMessage} />);
      expect(screen.getByText('Thinking...')).toBeInTheDocument();
    });
  });

  describe('MessageBubble Router', () => {
    it('renders UserMessageBubble for user role', () => {
      render(<MessageBubble message={mockUserMessage} />);
      expect(screen.getByText(mockUserMessage.content)).toBeInTheDocument();
    });

    it('renders AgentMessageBubble for assistant role', () => {
      render(<MessageBubble message={mockAgentMessage} />);
      expect(screen.getByText(mockAgentMessage.content)).toBeInTheDocument();
    });
  });

  describe('Regression Prevention', () => {
    it('user message Card does not use default Shadcn py-6 padding', () => {
      const { container } = render(<UserMessageBubble message={mockUserMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      
      // This test will fail if someone removes py-0 override
      expect(card?.classList.contains('py-0')).toBe(true);
    });

    it('agent message Card does not use default Shadcn py-6 padding', () => {
      const { container } = render(<AgentMessageBubble message={mockAgentMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      
      // This test will fail if someone removes py-0 override
      expect(card?.classList.contains('py-0')).toBe(true);
    });

    it('maintains compact CardContent padding of p-3', () => {
      const { container } = render(<UserMessageBubble message={mockUserMessage} />);
      const cardContent = container.querySelector('[data-slot="card-content"]');
      
      // CardContent should use p-3, not default px-6 from Shadcn
      expect(cardContent?.classList.contains('p-3')).toBe(true);
    });
  });

  describe('Height Consistency', () => {
    it('user message bubble has consistent height', () => {
      const { container } = render(<UserMessageBubble message={mockUserMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      
      // Verify Card has flex layout from Shadcn
      expect(card).toHaveClass('flex');
      expect(card).toHaveClass('flex-col');
      
      // Verify custom py-0 overrides default py-6
      expect(card).toHaveClass('py-0');
    });

    it('agent message bubble has consistent height', () => {
      const { container } = render(<AgentMessageBubble message={mockAgentMessage} />);
      const card = container.querySelector('[data-slot="card"]');
      
      // Verify Card has flex layout from Shadcn
      expect(card).toHaveClass('flex');
      expect(card).toHaveClass('flex-col');
      
      // Verify custom py-0 overrides default py-6
      expect(card).toHaveClass('py-0');
    });
  });
});
