/**
 * Mock Settings Service
 * 
 * Provides mock data for agent settings until backend API is ready
 */

import { AgentSettings, AgentType } from '@/types/settings';

/**
 * Mock agent settings data
 */
const mockAgentSettings: AgentSettings[] = [
  {
    id: 'chat-agent-1',
    name: 'General Chat Agent',
    type: 'chat',
    description: 'General-purpose conversational AI agent for answering questions and providing assistance',
    enabled: true,
    configuration: {
      model: 'llama3.2:latest',
      provider: 'ollama',
      temperature: 0.7,
      maxTokens: 2048,
      tools: ['web_search', 'calculator', 'code_interpreter'],
      systemPrompt: 'You are a helpful AI assistant. Be concise and accurate in your responses.',
    },
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-09T10:00:00Z',
  },
  {
    id: 'canvas-agent-1',
    name: 'Canvas Agent',
    type: 'canvas',
    description: 'Specialized agent for creating and editing visual content, diagrams, and collaborative workspaces',
    enabled: true,
    configuration: {
      model: 'gpt-4',
      provider: 'openai',
      temperature: 0.8,
      maxTokens: 4096,
      tools: ['canvas_editor', 'image_generation', 'diagram_tools'],
      customInstructions: 'Focus on creating clear, visually appealing content. Always ask for clarification on ambiguous requests.',
    },
    createdAt: '2024-01-02T00:00:00Z',
    updatedAt: '2024-01-08T15:30:00Z',
  },
  {
    id: 'insurance-agent-1',
    name: 'Insurance Claims Agent',
    type: 'insurance',
    description: 'Domain-specific agent for processing insurance claims, policy queries, and customer support',
    enabled: true,
    configuration: {
      model: 'claude-3-sonnet',
      provider: 'anthropic',
      temperature: 0.3,
      maxTokens: 3000,
      tools: ['policy_lookup', 'claims_processor', 'document_analyzer'],
      systemPrompt: 'You are an insurance specialist. Provide accurate policy information and guide customers through claims processes.',
      customInstructions: 'Always verify policy numbers and maintain confidentiality of customer data.',
    },
    createdAt: '2024-01-03T00:00:00Z',
    updatedAt: '2024-01-09T08:15:00Z',
  },
  {
    id: 'salary-viewer-agent-1',
    name: 'Salary Viewer Agent',
    type: 'salary_viewer',
    description: 'Specialized agent for analyzing salary data, compensation trends, and HR analytics',
    enabled: false,
    configuration: {
      model: 'gemini-pro',
      provider: 'gemini',
      temperature: 0.5,
      maxTokens: 2048,
      tools: ['data_analysis', 'chart_generator', 'salary_comparator'],
      customInstructions: 'Provide clear salary insights and visualizations. Respect data privacy and confidentiality.',
    },
    createdAt: '2024-01-04T00:00:00Z',
    updatedAt: '2024-01-05T12:00:00Z',
  },
  {
    id: 'a2ui-agent-1',
    name: 'A2UI Interactive Agent',
    type: 'a2ui',
    description: 'Agent-to-UI protocol agent for building interactive user interfaces and dynamic components',
    enabled: true,
    configuration: {
      model: 'llama3.2:latest',
      provider: 'ollama',
      temperature: 0.6,
      maxTokens: 2048,
      tools: ['ui_builder', 'component_generator', 'form_handler'],
      systemPrompt: 'You create interactive UI components. Generate JSON configurations for A2UI protocol.',
    },
    createdAt: '2024-01-05T00:00:00Z',
    updatedAt: '2024-01-09T09:45:00Z',
  },
  {
    id: 'custom-agent-1',
    name: 'Research Assistant',
    type: 'custom',
    description: 'Custom agent for in-depth research, citation management, and academic writing support',
    enabled: true,
    configuration: {
      model: 'gpt-4-turbo',
      provider: 'openai',
      temperature: 0.4,
      maxTokens: 8192,
      tools: ['web_search', 'citation_generator', 'fact_checker', 'summarizer'],
      systemPrompt: 'You are a research assistant. Provide well-cited, accurate information with sources.',
      customInstructions: 'Always cite sources. Prioritize peer-reviewed and authoritative sources.',
    },
    createdAt: '2024-01-06T00:00:00Z',
    updatedAt: '2024-01-07T14:20:00Z',
  },
];

/**
 * Simulated API delay
 */
const MOCK_API_DELAY = 500;

/**
 * Mock API: Get all agent settings
 */
export async function getMockAgentSettings(): Promise<AgentSettings[]> {
  await new Promise(resolve => setTimeout(resolve, MOCK_API_DELAY));
  return [...mockAgentSettings];
}

/**
 * Mock API: Get single agent settings by ID
 */
export async function getMockAgentSettingsById(id: string): Promise<AgentSettings | null> {
  await new Promise(resolve => setTimeout(resolve, MOCK_API_DELAY));
  const agent = mockAgentSettings.find(a => a.id === id);
  return agent ? { ...agent } : null;
}

/**
 * Mock API: Update agent settings
 */
export async function updateMockAgentSettings(
  id: string,
  updates: Partial<AgentSettings>
): Promise<AgentSettings> {
  await new Promise(resolve => setTimeout(resolve, MOCK_API_DELAY));
  
  const index = mockAgentSettings.findIndex(a => a.id === id);
  if (index === -1) {
    throw new Error(`Agent with id ${id} not found`);
  }
  
  const updatedAgent: AgentSettings = {
    ...mockAgentSettings[index],
    ...updates,
    updatedAt: new Date().toISOString(),
  };
  
  mockAgentSettings[index] = updatedAgent;
  return { ...updatedAgent };
}

/**
 * Available LLM models by provider (for select dropdowns)
 */
export const AVAILABLE_MODELS: Record<string, string[]> = {
  ollama: ['llama3.2:latest', 'llama3.1:latest', 'mistral:latest', 'codellama:latest'],
  openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
  gemini: ['gemini-pro', 'gemini-ultra'],
  azure: ['azure-gpt-4', 'azure-gpt-35-turbo'],
};

/**
 * Available tools (for multi-select)
 */
export const AVAILABLE_TOOLS = [
  'web_search',
  'calculator',
  'code_interpreter',
  'canvas_editor',
  'image_generation',
  'diagram_tools',
  'policy_lookup',
  'claims_processor',
  'document_analyzer',
  'data_analysis',
  'chart_generator',
  'salary_comparator',
  'ui_builder',
  'component_generator',
  'form_handler',
  'citation_generator',
  'fact_checker',
  'summarizer',
];
