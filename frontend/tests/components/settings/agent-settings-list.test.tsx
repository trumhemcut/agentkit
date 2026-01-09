import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentSettingsList } from '@/components/settings/agent-settings-list';
import { useSettingsStore } from '@/stores/settingsStore';
import { AgentSettings } from '@/types/settings';

// Mock the settings store
jest.mock('@/stores/settingsStore', () => ({
  useSettingsStore: jest.fn(),
}));

// Mock the settings card component
jest.mock('@/components/settings/agent-settings-card', () => ({
  AgentSettingsCard: ({ agent }: { agent: AgentSettings }) => (
    <div data-testid={`agent-card-${agent.id}`}>{agent.name}</div>
  ),
}));

describe('AgentSettingsList', () => {
  const mockLoadAgents = jest.fn();
  
  const mockAgents: AgentSettings[] = [
    {
      id: 'agent-1',
      name: 'Test Agent 1',
      type: 'chat',
      description: 'Test description 1',
      enabled: true,
      configuration: {
        model: 'test-model',
        provider: 'ollama',
      },
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    {
      id: 'agent-2',
      name: 'Test Agent 2',
      type: 'canvas',
      description: 'Test description 2',
      enabled: false,
      configuration: {
        model: 'test-model-2',
        provider: 'openai',
      },
      createdAt: '2024-01-02T00:00:00Z',
      updatedAt: '2024-01-02T00:00:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state', () => {
    (useSettingsStore as unknown as jest.Mock).mockReturnValue({
      agents: [],
      loading: true,
      loadAgents: mockLoadAgents,
    });

    render(<AgentSettingsList />);

    expect(screen.getByText(/loading agent settings/i)).toBeInTheDocument();
  });

  it('should render empty state when no agents', () => {
    (useSettingsStore as unknown as jest.Mock).mockReturnValue({
      agents: [],
      loading: false,
      loadAgents: mockLoadAgents,
    });

    render(<AgentSettingsList />);

    expect(screen.getByText(/no agents configured/i)).toBeInTheDocument();
  });

  it('should render agent cards when agents are loaded', () => {
    (useSettingsStore as unknown as jest.Mock).mockReturnValue({
      agents: mockAgents,
      loading: false,
      loadAgents: mockLoadAgents,
    });

    render(<AgentSettingsList />);

    expect(screen.getByTestId('agent-card-agent-1')).toBeInTheDocument();
    expect(screen.getByTestId('agent-card-agent-2')).toBeInTheDocument();
    expect(screen.getByText('Test Agent 1')).toBeInTheDocument();
    expect(screen.getByText('Test Agent 2')).toBeInTheDocument();
  });

  it('should call loadAgents on mount if agents are empty', async () => {
    (useSettingsStore as unknown as jest.Mock).mockReturnValue({
      agents: [],
      loading: false,
      loadAgents: mockLoadAgents,
    });

    render(<AgentSettingsList />);

    await waitFor(() => {
      expect(mockLoadAgents).toHaveBeenCalledTimes(1);
    });
  });

  it('should not call loadAgents if agents already exist', () => {
    (useSettingsStore as unknown as jest.Mock).mockReturnValue({
      agents: mockAgents,
      loading: false,
      loadAgents: mockLoadAgents,
    });

    render(<AgentSettingsList />);

    expect(mockLoadAgents).not.toHaveBeenCalled();
  });
});
