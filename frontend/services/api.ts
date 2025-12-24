/**
 * API Client for backend communication
 * 
 * Provides typed functions for interacting with the backend API endpoints.
 * Handles AG-UI protocol streaming events from the backend.
 */

import { ArtifactV3, SelectedText } from '@/types/canvas';
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
  agent: string | undefined,
  onEvent: (event: any) => void
): Promise<void> {
  try {
    const chatRequest: ChatRequest = {
      thread_id: threadId,
      run_id: runId,
      messages: messages,
      model: model,
      agent: agent,
    };

    console.log('[API] Sending chat request:', { threadId, runId, messageCount: messages.length, model, agent });

    const response = await fetch(`${API_BASE_URL}/api/chat`, {
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
  artifact?: ArtifactV3;
  selectedText?: SelectedText;
  action?: "create" | "update" | "rewrite" | "chat";
  model?: string;
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
  artifact: ArtifactV3 | undefined,
  selectedText: SelectedText | undefined,
  action: "create" | "update" | "rewrite" | "chat" | undefined,
  model: string | undefined,
  agent: string | undefined,
  onEvent: (event: any) => void
): Promise<void> {
  try {
    const canvasRequest: CanvasRequest = {
      thread_id: threadId,
      run_id: runId,
      messages: messages,
      artifact: artifact,
      selectedText: selectedText,
      action: action,
      model: model,
      agent: agent,
    };

    console.log('[API] Sending canvas request:', { 
      threadId, 
      runId, 
      messageCount: messages.length,
      hasArtifact: !!artifact,
      action,
      model,
      agent
    });

    const response = await fetch(`${API_BASE_URL}/api/canvas/stream`, {
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
  try {
    console.log('[API] Fetching available agents...');
    const response = await fetch(`${API_BASE_URL}/api/agents`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch agents: ${response.statusText}`);
    }
    
    const data: AgentsResponse = await response.json();
    console.log('[API] Available agents:', data);
    return data;
  } catch (error) {
    console.error('[API] Error fetching agents:', error);
    // Return default fallback if API fails
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
      models: [
        {
          id: 'qwen:7b',
          name: 'Qwen 7B',
          size: '7B parameters',
          available: true
        }
      ],
      default: 'qwen:7b'
    };
  }
}
