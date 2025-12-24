// Chat message types
export type MessageType = 'text' | 'artifact';

export interface Message {
  id: string;
  threadId: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  agentName?: string;
  isStreaming?: boolean;
  isPending?: boolean; // True when waiting for server response
  
  // Message type field
  messageType?: MessageType; // Defaults to 'text' if not specified
  
  // Artifact-specific fields (only when messageType === 'artifact')
  artifactType?: 'code' | 'text' | 'document';
  language?: string;  // for code artifacts
  title?: string;
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
}

// Chat conversation state
export interface ConversationState {
  currentThreadId: string | null;
  threads: Thread[];
  isLoading: boolean;
  error: string | null;
}

// LLM Model types
export interface LLMModel {
  id: string;
  name: string;
  size: string;
  available: boolean;
}

export interface ModelsResponse {
  models: LLMModel[];
  default: string;
}
