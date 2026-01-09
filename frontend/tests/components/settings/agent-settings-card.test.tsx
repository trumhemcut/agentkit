import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentSettingsCard } from '@/components/settings/agent-settings-card';
import { useSettingsStore } from '@/stores/settingsStore';
import { AgentSettings } from '@/types/settings';

// Mock the settings store
jest.mock('@/stores/settingsStore', () => ({
  useSettingsStore: jest.fn(),
}));

// Mock the settings form component
jest.mock('@/components/settings/agent-settings-form', () => ({
  AgentSettingsForm: ({ agent }: { agent: AgentSettings }) => (
    <div data-testid="settings-form">Settings form for {agent.name}</div>
  ),
}));

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe('AgentSettingsCard', () => {
  const mockUpdateAgent = jest.fn();

  const mockAgent: AgentSettings = {
    id: 'test-agent',
    name: 'Test Agent',
    type: 'chat',
    description: 'Test agent description',
    enabled: true,
    configuration: {
      model: 'test-model',
      provider: 'ollama',
      temperature: 0.7,
      maxTokens: 2048,
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

  it('should render agent information', () => {
    render(<AgentSettingsCard agent={mockAgent} />);

    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('Test agent description')).toBeInTheDocument();
    expect(screen.getByText('chat')).toBeInTheDocument();
    expect(screen.getByText('Enabled')).toBeInTheDocument();
    expect(screen.getByText(/Model: test-model/i)).toBeInTheDocument();
    expect(screen.getByText(/Provider: ollama/i)).toBeInTheDocument();
  });

  it('should render disabled state correctly', () => {
    const disabledAgent = { ...mockAgent, enabled: false };
    render(<AgentSettingsCard agent={disabledAgent} />);

    expect(screen.getByText('Disabled')).toBeInTheDocument();
  });

  it('should expand and collapse settings form', () => {
    render(<AgentSettingsCard agent={mockAgent} />);

    // Initially collapsed
    expect(screen.queryByTestId('settings-form')).not.toBeInTheDocument();

    // Expand
    const expandButton = screen.getByRole('button', { name: /expand settings/i });
    fireEvent.click(expandButton);
    expect(screen.getByTestId('settings-form')).toBeInTheDocument();

    // Collapse
    const collapseButton = screen.getByRole('button', { name: /collapse settings/i });
    fireEvent.click(collapseButton);
    expect(screen.queryByTestId('settings-form')).not.toBeInTheDocument();
  });

  it('should render toggle switch for enabled state', () => {
    render(<AgentSettingsCard agent={mockAgent} />);

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeInTheDocument();
    expect(toggle).toBeChecked();
  });

  it('should display correct badge color for agent type', () => {
    const { rerender } = render(<AgentSettingsCard agent={mockAgent} />);
    expect(screen.getByText('chat')).toHaveClass('text-blue-800');

    const canvasAgent = { ...mockAgent, type: 'canvas' as const };
    rerender(<AgentSettingsCard agent={canvasAgent} />);
    expect(screen.getByText('canvas')).toHaveClass('text-purple-800');
  });
});
