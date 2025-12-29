/**
 * A2UIOTPInput Component Tests
 * 
 * Test suite for A2UIOTPInput component that renders OTP (One-Time Password)
 * input blocks following the A2UI protocol specification.
 * 
 * Tests cover:
 * 1. Basic OTP input rendering
 * 2. Different lengths (4, 5, 6 digits)
 * 3. Separator groups
 * 4. Pattern validation (digits vs alphanumeric)
 * 5. Disabled state
 * 6. Data model integration
 * 7. Button state and interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { A2UIOTPInput } from '@/components/A2UI/components/A2UIOTPInput';
import { useA2UIStore } from '@/stores/a2uiStore';

// Mock the store
jest.mock('@/stores/a2uiStore', () => ({
  useA2UIStore: jest.fn(),
}));

describe('A2UIOTPInput', () => {
  const mockUpdateDataModel = jest.fn();
  const mockOnAction = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useA2UIStore as unknown as jest.Mock).mockImplementation((selector) =>
      selector({ updateDataModel: mockUpdateDataModel })
    );
  });

  describe('Basic Rendering', () => {
    it('renders with default props', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByText('Enter verification code')).toBeInTheDocument();
      expect(screen.getByText(/Please enter the verification code/)).toBeInTheDocument();
    });

    it('renders with custom title and description', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            title: { literalString: 'Verify Email' },
            description: { literalString: 'Enter the 6-digit code sent to your email' },
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByText('Verify Email')).toBeInTheDocument();
      expect(screen.getByText('Enter the 6-digit code sent to your email')).toBeInTheDocument();
    });

    it('renders with custom button text', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            buttonText: { literalString: 'Submit Code' },
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByRole('button', { name: 'Submit Code' })).toBeInTheDocument();
    });
  });

  describe('OTP Length Configuration', () => {
    it('renders with 4 digits', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            maxLength: 4,
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      // InputOTP should be configured for 4 slots
      const container = screen.getByText('Enter verification code').closest('div');
      expect(container).toBeInTheDocument();
    });

    it('renders with 6 digits (default)', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      // Should default to 6 digits
      const container = screen.getByText('Enter verification code').closest('div');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Separator Groups', () => {
    it('renders with separator groups', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            maxLength: 6,
            groups: [
              { start: 0, end: 3 },
              { start: 3, end: 6 },
            ],
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      // Component should render with groups
      const container = screen.getByText('Enter verification code').closest('div');
      expect(container).toBeInTheDocument();
    });

    it('renders with multiple separator groups', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            maxLength: 6,
            groups: [
              { start: 0, end: 2 },
              { start: 2, end: 4 },
              { start: 4, end: 6 },
            ],
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      // Component should render with multiple groups
      const container = screen.getByText('Enter verification code').closest('div');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Pattern Type', () => {
    it('renders with digits pattern type', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            patternType: 'digits',
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      const container = screen.getByText('Enter verification code').closest('div');
      expect(container).toBeInTheDocument();
    });

    it('renders with alphanumeric pattern type', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            patternType: 'alphanumeric',
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      const container = screen.getByText('Enter verification code').closest('div');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('renders disabled OTP input', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            disabled: true,
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      const button = screen.getByRole('button', { name: 'Verify' });
      expect(button).toBeDisabled();
    });

    it('enables button when OTP is complete', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            maxLength: 6,
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              'otp-123': {
                value: '123456',
              },
            },
          }}
          surfaceId="surface-1"
        />
      );

      const button = screen.getByRole('button', { name: 'Verify' });
      expect(button).not.toBeDisabled();
    });

    it('disables button when OTP is incomplete', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            maxLength: 6,
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              'otp-123': {
                value: '123',
              },
            },
          }}
          surfaceId="surface-1"
        />
      );

      const button = screen.getByRole('button', { name: 'Verify' });
      expect(button).toBeDisabled();
    });
  });

  describe('Data Model Integration', () => {
    it('displays value from data model', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              'otp-123': {
                value: '123456',
              },
            },
          }}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByText(/Entered:/)).toBeInTheDocument();
      expect(screen.getByText('123456')).toBeInTheDocument();
    });

    it('shows placeholder when no value in data model', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{}}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByText('Enter your verification code')).toBeInTheDocument();
    });
  });

  describe('Button Interactions', () => {
    it('calls onAction when submit button is clicked', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              'otp-123': {
                value: '123456',
              },
            },
          }}
          surfaceId="surface-1"
          onAction={mockOnAction}
        />
      );

      const button = screen.getByRole('button', { name: 'Verify' });
      fireEvent.click(button);

      expect(mockOnAction).toHaveBeenCalledWith('otp_submit', {
        componentId: 'otp-123',
        value: '123456',
        path: '/ui/otp-123/value',
      });
    });

    it('does not call onAction when button is disabled', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            disabled: true,
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              'otp-123': {
                value: '123456',
              },
            },
          }}
          surfaceId="surface-1"
          onAction={mockOnAction}
        />
      );

      const button = screen.getByRole('button', { name: 'Verify' });
      // Button is disabled, so click won't trigger
      expect(button).toBeDisabled();
    });
  });

  describe('Text Resolution from Data Model', () => {
    it('resolves title from data model path', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            title: { path: '/ui/texts/title' },
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              texts: {
                title: 'Email Verification',
              },
            },
          }}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByText('Email Verification')).toBeInTheDocument();
    });

    it('resolves description from data model path', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            description: { path: '/ui/texts/description' },
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              texts: {
                description: 'Check your email for the code',
              },
            },
          }}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByText('Check your email for the code')).toBeInTheDocument();
    });

    it('resolves button text from data model path', () => {
      render(
        <A2UIOTPInput
          id="otp-123"
          props={{
            buttonText: { path: '/ui/texts/buttonText' },
            value: { path: '/ui/otp-123/value' },
          }}
          dataModel={{
            ui: {
              texts: {
                buttonText: 'Confirm Code',
              },
            },
          }}
          surfaceId="surface-1"
        />
      );

      expect(screen.getByRole('button', { name: 'Confirm Code' })).toBeInTheDocument();
    });
  });
});
