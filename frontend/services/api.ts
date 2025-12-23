/**
 * API Client for backend communication
 * 
 * Provides typed functions for interacting with the backend API endpoints.
 * Handles AG-UI protocol streaming events from the backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Message {
  role: string;
  content: string;
}

export interface ChatRequest {
  thread_id: string;
  run_id: string;
  messages: Message[];
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
 * @param onEvent - Callback function to handle each AG-UI event
 */
export async function sendChatMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  onEvent: (event: any) => void
): Promise<void> {
  try {
    const chatRequest: ChatRequest = {
      thread_id: threadId,
      run_id: runId,
      messages: messages,
    };

    console.log('[API] Sending chat request:', { threadId, runId, messageCount: messages.length });

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
