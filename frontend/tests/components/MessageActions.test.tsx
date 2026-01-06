/**
 * Tests for MessageActions component
 * 
 * Tests copy, like, dislike, and retry functionality
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MessageActions } from '@/components/MessageActions';
import { toast } from 'sonner';
import * as api from '@/services/api';

// Mock dependencies
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('@/services/api', () => ({
  submitMessageFeedback: jest.fn(),
  removeMessageFeedback: jest.fn(),
  getMessageFeedback: jest.fn(),
}));

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve()),
  },
});

describe('MessageActions', () => {
  const defaultProps = {
    messageId: 'test-message-id',
    messageContent: 'This is a test message content',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getMessageFeedback as jest.Mock).mockResolvedValue({ feedback_type: null });
  });

  describe('Copy functionality', () => {
    it('should copy message content to clipboard', async () => {
      render(<MessageActions {...defaultProps} />);
      
      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(defaultProps.messageContent);
        expect(toast.success).toHaveBeenCalledWith('Copied to clipboard');
      });
    });

    it('should show error toast when copy fails', async () => {
      (navigator.clipboard.writeText as jest.Mock).mockRejectedValue(new Error('Copy failed'));
      
      render(<MessageActions {...defaultProps} />);
      
      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to copy');
      });
    });
  });

  describe('Like functionality', () => {
    it('should submit like feedback', async () => {
      (api.submitMessageFeedback as jest.Mock).mockResolvedValue(undefined);
      
      render(<MessageActions {...defaultProps} />);
      
      await waitFor(() => {
        const likeButton = screen.getByTitle('Good response');
        fireEvent.click(likeButton);
      });
      
      await waitFor(() => {
        expect(api.submitMessageFeedback).toHaveBeenCalledWith(defaultProps.messageId, 'like');
      });
    });

    it('should toggle like feedback when clicked again', async () => {
      (api.submitMessageFeedback as jest.Mock).mockResolvedValue(undefined);
      (api.removeMessageFeedback as jest.Mock).mockResolvedValue(undefined);
      (api.getMessageFeedback as jest.Mock).mockResolvedValue({ feedback_type: 'like' });
      
      render(<MessageActions {...defaultProps} />);
      
      await waitFor(() => {
        const likeButton = screen.getByTitle('Good response');
        expect(likeButton).toHaveClass('text-green-600');
      });
      
      const likeButton = screen.getByTitle('Good response');
      fireEvent.click(likeButton);
      
      await waitFor(() => {
        expect(api.removeMessageFeedback).toHaveBeenCalledWith(defaultProps.messageId);
      });
    });

    it('should show error toast when like submission fails', async () => {
      (api.submitMessageFeedback as jest.Mock).mockRejectedValue(new Error('Submit failed'));
      
      render(<MessageActions {...defaultProps} />);
      
      await waitFor(() => {
        const likeButton = screen.getByTitle('Good response');
        fireEvent.click(likeButton);
      });
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to submit feedback');
      });
    });
  });

  describe('Dislike functionality', () => {
    it('should submit dislike feedback', async () => {
      (api.submitMessageFeedback as jest.Mock).mockResolvedValue(undefined);
      
      render(<MessageActions {...defaultProps} />);
      
      await waitFor(() => {
        const dislikeButton = screen.getByTitle('Bad response');
        fireEvent.click(dislikeButton);
      });
      
      await waitFor(() => {
        expect(api.submitMessageFeedback).toHaveBeenCalledWith(defaultProps.messageId, 'dislike');
      });
    });

    it('should toggle dislike feedback when clicked again', async () => {
      (api.submitMessageFeedback as jest.Mock).mockResolvedValue(undefined);
      (api.removeMessageFeedback as jest.Mock).mockResolvedValue(undefined);
      (api.getMessageFeedback as jest.Mock).mockResolvedValue({ feedback_type: 'dislike' });
      
      render(<MessageActions {...defaultProps} />);
      
      await waitFor(() => {
        const dislikeButton = screen.getByTitle('Bad response');
        expect(dislikeButton).toHaveClass('text-red-600');
      });
      
      const dislikeButton = screen.getByTitle('Bad response');
      fireEvent.click(dislikeButton);
      
      await waitFor(() => {
        expect(api.removeMessageFeedback).toHaveBeenCalledWith(defaultProps.messageId);
      });
    });
  });

  describe('Retry functionality', () => {
    it('should call onRetry callback when retry button is clicked', () => {
      const onRetry = jest.fn();
      
      render(<MessageActions {...defaultProps} onRetry={onRetry} />);
      
      const retryButton = screen.getByTitle('Regenerate response');
      fireEvent.click(retryButton);
      
      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should not render retry button when onRetry is not provided', () => {
      render(<MessageActions {...defaultProps} />);
      
      const retryButton = screen.queryByTitle('Regenerate response');
      expect(retryButton).not.toBeInTheDocument();
    });
  });

  describe('Initial feedback state', () => {
    it('should load feedback state from API on mount', async () => {
      (api.getMessageFeedback as jest.Mock).mockResolvedValue({ feedback_type: 'like' });
      
      render(<MessageActions {...defaultProps} />);
      
      await waitFor(() => {
        expect(api.getMessageFeedback).toHaveBeenCalledWith(defaultProps.messageId);
      });
      
      await waitFor(() => {
        const likeButton = screen.getByTitle('Good response');
        expect(likeButton).toHaveClass('text-green-600');
      });
    });

    it('should use initialFeedback prop if provided', () => {
      render(<MessageActions {...defaultProps} initialFeedback="dislike" />);
      
      const dislikeButton = screen.getByTitle('Bad response');
      expect(dislikeButton).toHaveClass('text-red-600');
    });
  });

  describe('Button states', () => {
    it('should disable feedback buttons while submitting', async () => {
      let resolveSubmit: (value: void) => void;
      const submitPromise = new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      });
      
      (api.submitMessageFeedback as jest.Mock).mockReturnValue(submitPromise);
      
      render(<MessageActions {...defaultProps} />);
      
      await waitFor(() => {
        const likeButton = screen.getByTitle('Good response');
        fireEvent.click(likeButton);
      });
      
      const likeButton = screen.getByTitle('Good response');
      const dislikeButton = screen.getByTitle('Bad response');
      
      expect(likeButton).toBeDisabled();
      expect(dislikeButton).toBeDisabled();
      
      // Resolve the promise to cleanup
      resolveSubmit!();
    });
  });
});
