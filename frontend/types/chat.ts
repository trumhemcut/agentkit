// Chat message types
export interface Message {
  id: string;
  threadId: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  agentName?: string;
  isStreaming?: boolean;
  isPending?: boolean; // True when waiting for server response
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
