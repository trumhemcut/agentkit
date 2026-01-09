/**
 * Settings Types
 * 
 * TypeScript interfaces for agent settings and configuration
 */

export type AgentType = 'chat' | 'canvas' | 'insurance' | 'salary_viewer' | 'a2ui' | 'custom';

export type LLMProvider = 'ollama' | 'openai' | 'azure' | 'gemini' | 'anthropic';

export interface AgentConfiguration {
  model?: string;
  provider?: LLMProvider;
  temperature?: number;
  maxTokens?: number;
  tools?: string[];
  customInstructions?: string;
  systemPrompt?: string;
  // Additional configuration fields
  [key: string]: unknown;
}

export interface AgentSettings {
  id: string;
  name: string;
  type: AgentType;
  description: string;
  enabled: boolean;
  configuration: AgentConfiguration;
  createdAt: string;
  updatedAt: string;
}

export interface AgentSettingsFormData {
  name: string;
  description: string;
  enabled: boolean;
  model?: string;
  provider?: LLMProvider;
  temperature?: number;
  maxTokens?: number;
  tools?: string[];
  customInstructions?: string;
  systemPrompt?: string;
}

export interface SettingsStore {
  // State
  agents: AgentSettings[];
  loading: boolean;
  error: string | null;
  selectedAgentId: string | null;
  
  // Actions
  loadAgents: () => Promise<void>;
  updateAgent: (id: string, settings: Partial<AgentSettings>) => Promise<void>;
  setSelectedAgent: (id: string | null) => void;
  reset: () => void;
}
