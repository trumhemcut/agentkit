/**
 * API Client for backend communication
 * 
 * Provides typed functions for interacting with the backend API endpoints.
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
 * Send a chat message to the backend and get streaming response
 * Returns a ReadableStream that can be consumed for SSE events
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

    console.log('Sending chat request:', chatRequest);

    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(chatRequest),
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));

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

    console.log('Starting to read stream...');

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        console.log('Stream completed');
        break;
      }

      // Decode chunk and add to buffer
      const chunk = decoder.decode(value, { stream: true });
      console.log('Received chunk:', chunk);
      buffer += chunk;

      // Process complete SSE messages
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // Remove 'data: ' prefix
          
          if (data.trim() === '[DONE]') {
            continue;
          }

          try {
            const event = JSON.parse(data);
            console.log('Parsed event:', event);
            onEvent(event);
          } catch (error) {
            console.error('Error parsing SSE event:', error, data);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error sending chat message:', error);
    onEvent({
      type: 'ERROR',
      data: { message: error instanceof Error ? error.message : 'Unknown error' },
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
