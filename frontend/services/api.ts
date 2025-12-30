/**
 * API Client for backend communication
 * 
 * Provides typed functions for interacting with the backend API endpoints.
 * Handles AG-UI protocol streaming events from the backend.
 */

import { Artifact, SelectedText } from '@/types/canvas';
import { LLMModel, ModelsResponse } from '@/types/chat';
import { AgentsResponse } from '@/types/agent';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Message {
  role: string;
  content: string;
}

export interface ChatRequest {
  thread_id: string;
  run_id: string;
  messages: Message[];
  model?: string;
  provider?: string;  // Provider selection
  agent?: string;
}

export interface AgentStatusResponse {
  agentId: string;
  status: string;
  lastUpdate: number;
}

/**
 * Send a chat message to the backend and get streaming AG-UI response
 * 
 * This function sends a POST request to the /api/chat endpoint and processes
 * the Server-Sent Events (SSE) stream returned by the backend.
 * 
 * @param messages - Array of messages in the conversation
 * @param threadId - Unique identifier for the conversation thread
 * @param runId - Unique identifier for this agent run
 * @param model - Optional LLM model ID to use for this conversation
 * @param agent - Optional agent ID to use for this conversation
 * @param onEvent - Callback function to handle each AG-UI event
 */
export async function sendChatMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  model: string | undefined,
  provider: string | undefined,
  agent: string | undefined,
  onEvent: (event: any) => void
): Promise<void> {
  try {
    // Use the unified endpoint pattern: /chat/{agent_id}
    // Default to 'chat' if no agent specified (matches agent_registry IDs)
    const agentId = agent || 'chat';
    
    const chatRequest: ChatRequest = {
      thread_id: threadId,
      run_id: runId,
      messages: messages,
      model: model,
      provider: provider,  // Include provider
      agent: agentId, // Keep for backward compatibility
    };

    console.log('[API] Sending chat request:', { threadId, runId, messageCount: messages.length, model, provider, agent: agentId });

    const response = await fetch(`${API_BASE_URL}/api/chat/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(chatRequest),
    });

    console.log('[API] Response status:', response.status);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Process SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    console.log('[API] Starting to read AG-UI event stream...');

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        console.log('[API] Stream completed');
        break;
      }

      // Decode chunk and add to buffer
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // Process complete SSE messages
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        // SSE format: "data: <json>"
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // Remove 'data: ' prefix
          
          // Skip [DONE] marker
          if (data.trim() === '[DONE]') {
            continue;
          }

          try {
            const event = JSON.parse(data);
            console.log('[API] Received AG-UI event:', event.type);
            onEvent(event);
          } catch (error) {
            console.error('[API] Error parsing SSE event:', error, 'Data:', data);
          }
        }
      }
    }
  } catch (error) {
    console.error('[API] Error sending chat message:', error);
    onEvent({
      type: 'ERROR',
      message: error instanceof Error ? error.message : 'Unknown error',
      timestamp: Date.now(),
    });
  }
}

/**
 * Get agent status
 */
export async function getAgentStatus(agentId: string): Promise<AgentStatusResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent/${agentId}/status`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting agent status:', error);
    return null;
  }
}

/**
 * Canvas API
 */

export interface CanvasRequest {
  thread_id: string;
  run_id: string;
  messages: Message[];
  artifact?: Artifact;
  artifact_id?: string;
  selectedText?: SelectedText;
  action?: "create" | "update" | "rewrite" | "chat";
  model?: string;
  provider?: string;  // Provider selection
  agent?: string;
}

/**
 * Send a canvas message to the backend and get streaming AG-UI response with artifacts
 * 
 * This function sends a POST request to the /api/canvas/stream endpoint and processes
 * the Server-Sent Events (SSE) stream returned by the backend.
 * 
 * @param messages - Array of messages in the conversation
 * @param threadId - Unique identifier for the conversation thread
 * @param runId - Unique identifier for this agent run
 * @param artifact - Current artifact state (if any)
 * @param selectedText - Selected text context (if any)
 * @param action - Explicit action to perform (create, update, rewrite, or chat)
 * @param model - Optional LLM model ID to use for this conversation
 * @param agent - Optional agent ID to use for this conversation
 * @param onEvent - Callback function to handle each AG-UI event
 */
export async function sendCanvasMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  artifact: Artifact | undefined,
  artifactId: string | undefined,
  selectedText: SelectedText | undefined,
  action: "create" | "update" | "rewrite" | "chat" | undefined,
  model: string | undefined,
  provider: string | undefined,
  agent: string | undefined,
  onEvent: (event: any) => void
): Promise<void> {
  try {
    // Use the unified endpoint pattern: /chat/{agent_id}
    // Agent ID must be provided from the /agents discovery API
    if (!agent) {
      throw new Error('Agent ID is required. Make sure agent selection is loaded from /agents API');
    }
    const agentId = agent;
    
    const canvasRequest: CanvasRequest = {
      thread_id: threadId,
      run_id: runId,
      messages: messages,
      artifact: artifact,
      artifact_id: artifactId,
      selectedText: selectedText,
      action: action,
      model: model,
      provider: provider,  // Include provider
      agent: agentId, // Keep for backward compatibility
    };

    console.log('[API] Sending canvas request:', { 
      threadId, 
      runId, 
      messageCount: messages.length,
      hasArtifact: !!artifact,
      artifactId: artifactId || 'undefined',
      action,
      model,
      provider,
      agent: agentId
    });

    const response = await fetch(`${API_BASE_URL}/api/chat/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(canvasRequest),
    });

    console.log('[API] Canvas response status:', response.status);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Process SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    console.log('[API] Starting to read Canvas AG-UI event stream...');

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        console.log('[API] Canvas stream completed');
        break;
      }

      // Decode chunk and add to buffer
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // Process complete SSE messages
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        // SSE format: "data: <json>"
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // Remove 'data: ' prefix
          
          // Skip [DONE] marker
          if (data.trim() === '[DONE]') {
            continue;
          }

          try {
            const event = JSON.parse(data);
            console.log('[API] Received Canvas AG-UI event:', event.type);
            onEvent(event);
          } catch (error) {
            console.error('[API] Error parsing Canvas SSE event:', error, 'Raw data:', data);
          }
        }
      }
    }
  } catch (error) {
    console.error('[API] Error sending canvas message:', error);
    onEvent({
      type: 'ERROR',
      message: error instanceof Error ? error.message : 'Unknown error',
      timestamp: Date.now(),
    });
  }
}

/**
 * Fetch available agents from backend
 * 
 * @returns Promise with AgentsResponse containing list of agents and default agent
 */
export async function fetchAvailableAgents(): Promise<AgentsResponse> {
  // Client-side only check
  if (typeof window === 'undefined') {
    console.warn('[API] fetchAvailableAgents called on server-side, returning defaults');
    return getDefaultAgentsResponse();
  }

  try {
    console.log('[API] Fetching available agents from:', `${API_BASE_URL}/api/agents`);
    const response = await fetch(`${API_BASE_URL}/api/agents`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch agents: ${response.statusText}`);
    }
    
    const data: AgentsResponse = await response.json();
    console.log('[API] Available agents loaded:', data.agents.length);
    return data;
  } catch (error) {
    console.error('[API] Error fetching agents:', error);
    console.warn('[API] Using fallback agents. Is backend running at', API_BASE_URL + '?');
    return getDefaultAgentsResponse();
  }
}

function getDefaultAgentsResponse(): AgentsResponse {
  return {
    agents: [
      {
        id: 'chat',
        name: 'Chat Agent',
        description: 'General purpose conversational agent',
        icon: 'message-circle',
        sub_agents: [],
        features: ['conversation', 'streaming']
      },
      {
        id: 'canvas',
        name: 'Canvas Agent',
        description: 'Multi-agent system with artifact generation and editing',
        icon: 'layout',
        sub_agents: ['generator', 'editor'],
        features: ['artifacts', 'code-generation', 'multi-step']
      }
    ],
    default: 'chat'
  };
}

/**
 * Fetch available LLM models from the backend
 * 
 * @returns Promise with ModelsResponse containing available models and default model
 */
export async function fetchAvailableModels(): Promise<ModelsResponse> {
  try {
    console.log('[API] Fetching available models...');
    const response = await fetch(`${API_BASE_URL}/api/models`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('[API] Available models:', data);
    return data;
  } catch (error) {
    console.error('[API] Error fetching models:', error);
    // Return default fallback if API fails
    return {
      providers: [
        {
          id: 'ollama',
          name: 'Ollama',
          available: true
        }
      ],
      models: [
        {
          id: 'qwen:7b',
          name: 'Qwen 7B',
          size: '7B parameters',
          available: true,
          provider: 'ollama'
        }
      ],
      default_provider: 'ollama',
      default_model: 'qwen:7b'
    };
  }
}

/**
 * Send a message to the salary viewer agent with A2UI support
 * 
 * This function sends a POST request to the salary-viewer agent endpoint
 * and processes the Server-Sent Events (SSE) stream with A2UI events.
 * 
 * @param messages - Array of messages in the conversation
 * @param threadId - Unique identifier for the conversation thread
 * @param runId - Unique identifier for this agent run
 * @param userInput - Optional user input from A2UI components (e.g., OTP code)
 * @param model - Optional LLM model ID to use
 * @param provider - Optional LLM provider
 * @param onEvent - Callback function to handle each event
 */
export async function sendSalaryViewerMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  userInput: string | undefined,
  model: string | undefined,
  provider: string | undefined,
  onEvent: (event: any) => void
): Promise<void> {
  try {
    const agentId = 'salary-viewer';
    
    const request = {
      thread_id: threadId,
      run_id: runId,
      messages: messages,
      user_input: userInput,
      model: model,
      provider: provider,
      agent: agentId,
    };

    console.log('[API] Sending salary viewer request:', { 
      threadId, 
      runId, 
      messageCount: messages.length,
      hasUserInput: !!userInput,
      model,
      provider
    });

    const response = await fetch(`${API_BASE_URL}/api/chat/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
    });

    console.log('[API] Salary viewer response status:', response.status);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Process SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    console.log('[API] Starting to read salary viewer event stream...');

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        console.log('[API] Stream complete');
        break;
      }

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });
      
      // Process complete events (delimited by double newline)
      const events = buffer.split('\n\n');
      buffer = events.pop() || ''; // Keep incomplete event in buffer

      for (const eventText of events) {
        if (!eventText.trim()) continue;

        try {
          // Parse SSE format: "data: {...}"
          const lines = eventText.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonData = line.substring(6);
              const event = JSON.parse(jsonData);
              onEvent(event);
            }
          }
        } catch (error) {
          console.error('[API] Error parsing event:', error, eventText);
        }
      }
    }
  } catch (error) {
    console.error('[API] Error in salary viewer chat:', error);
    throw error;
  }
}
