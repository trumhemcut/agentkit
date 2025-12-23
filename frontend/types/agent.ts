// Agent state types
export type AgentStatus = 'idle' | 'thinking' | 'executing' | 'complete' | 'error';

export interface AgentState {
  id: string;
  name: string;
  status: AgentStatus;
  currentTask?: string;
  lastUpdate: number;
}

// Agent metadata
export interface AgentMetadata {
  name: string;
  description: string;
  capabilities: string[];
  avatar?: string;
}
