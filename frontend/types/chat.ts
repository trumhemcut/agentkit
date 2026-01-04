// Chat message types
export type MessageType = 'text' | 'artifact';

export interface Message {
  id: string;
  threadId: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  agentName?: string;
  agentId?: string; // Agent ID (e.g., 'insurance-supervisor')
  isStreaming?: boolean;
  isPending?: boolean; // True when waiting for server response
  isInterrupted?: boolean; // True if user clicked Stop button
  
  // Message type field
  messageType?: MessageType; // Defaults to 'text' if not specified
  
  // Artifact-specific fields (only when messageType === 'artifact')
  artifactType?: 'code' | 'text' | 'document';
  language?: string;  // for code artifacts
  title?: string;
  artifactId?: string; // Artifact ID from backend
  
  // Metadata for agent-specific information
  metadata?: {
    selected_specialist?: string;
    specialist_name?: string;
    [key: string]: any;
  };
}

// Helper type guard
export function isArtifactMessage(message: Message): boolean {
  return message.messageType === 'artifact';
}

// Chat thread types
export interface Thread {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  artifactId?: string; // Canvas artifact ID for persistence
}

// Chat conversation state
export interface ConversationState {
  currentThreadId: string | null;
  threads: Thread[];
  isLoading: boolean;
  error: string | null;
}

// LLM Provider and Model types
export interface LLMProvider {
  id: string;
  name: string;
  available: boolean;
}

export interface LLMModel {
  id: string;
  name: string;
  size: string;
  available: boolean;
  provider: string;  // Provider association (e.g., "ollama", "gemini")
}

export interface ModelsResponse {
  providers: LLMProvider[];  // List of available providers
  models: LLMModel[];
  default_provider: string;  // Default provider (e.g., "ollama")
  default_model: string;
  errors?: Array<{ provider: string; error: string }>;
}
