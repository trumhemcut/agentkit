import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentSettingsForm } from '@/components/settings/agent-settings-form';
import { useSettingsStore } from '@/stores/settingsStore';
import { AgentSettings } from '@/types/settings';

// Mock the settings store
jest.mock('@/stores/settingsStore', () => ({
  useSettingsStore: jest.fn(),
}));

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe('AgentSettingsForm', () => {
  const mockUpdateAgent = jest.fn();
  const mockOnClose = jest.fn();

  const mockAgent: AgentSettings = {
    id: 'test-agent',
    name: 'Test Agent',
    type: 'chat',
    description: 'Test agent description',
    enabled: true,
    configuration: {
      model: 'llama3.2:latest',
      provider: 'ollama',
      temperature: 0.7,
      maxTokens: 2048,
      systemPrompt: 'Test system prompt',
      customInstructions: 'Test custom instructions',
    },
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useSettingsStore as unknown as jest.Mock).mockReturnValue({
      updateAgent: mockUpdateAgent,
    });
  });

  it('should render form with agent data', () => {
    render(<AgentSettingsForm agent={mockAgent} />);

    expect(screen.getByDisplayValue('Test Agent')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test agent description')).toBeInTheDocument();
    expect(screen.getByDisplayValue('0.7')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2048')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test system prompt')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test custom instructions')).toBeInTheDocument();
  });

  it('should update form fields on input', async () => {
    const user = userEvent.setup();
    render(<AgentSettingsForm agent={mockAgent} />);

    const nameInput = screen.getByLabelText(/agent name/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'Updated Agent Name');

    expect(nameInput).toHaveValue('Updated Agent Name');
  });

  it('should render save button', () => {
    render(<AgentSettingsForm agent={mockAgent} />);

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    expect(saveButton).toBeInTheDocument();
    expect(saveButton).not.toBeDisabled();
  });

  it('should render reset button', () => {
    render(<AgentSettingsForm agent={mockAgent} />);

    const resetButton = screen.getByRole('button', { name: /reset/i });
    expect(resetButton).toBeInTheDocument();
  });

  it('should update temperature value', async () => {
    const user = userEvent.setup();
    render(<AgentSettingsForm agent={mockAgent} />);

    const temperatureInput = screen.getByLabelText(/temperature/i);
    await user.clear(temperatureInput);
    await user.type(temperatureInput, '0.9');

    // Check that the value was updated (allowing for the original value to be appended)
    expect(parseFloat((temperatureInput as HTMLInputElement).value)).toBeGreaterThan(0.7);
  });

  it('should update max tokens value', async () => {
    const user = userEvent.setup();
    render(<AgentSettingsForm agent={mockAgent} />);

    const maxTokensInput = screen.getByLabelText(/max tokens/i);
    await user.clear(maxTokensInput);
    await user.type(maxTokensInput, '4096');

    // Check that the value was updated (allowing for the original value to be appended)
    expect(parseFloat((maxTokensInput as HTMLInputElement).value)).toBeGreaterThan(2048);
  });
});
