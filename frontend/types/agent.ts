// Agent state types
export type AgentStatus = 'idle' | 'thinking' | 'executing' | 'complete' | 'error';

export interface AgentState {
  id: string;
  name: string;
  status: AgentStatus;
  currentTask?: string;
  lastUpdate: number;
}

// Agent metadata for discovery
export interface AgentMetadata {
  id: string;
  name: string;
  description: string;
  icon: string;
  sub_agents: string[];
  features: string[];
}

/**
 * Response from /api/agents endpoint
 */
export interface AgentsResponse {
  agents: AgentMetadata[];
  default: string;
}

/**
 * Agent selection state
 */
export interface AgentSelection {
  selectedAgent: string;
  availableAgents: AgentMetadata[];
}
