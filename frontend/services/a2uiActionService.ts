/**
 * A2UI User Action Service
 * 
 * Handles sending user actions from A2UI components to the backend.
 * Implements client-to-server communication for A2UI v0.9 protocol.
 */

import type { UserAction, UserActionRequest } from '@/types/a2ui';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class A2UIUserActionService {
  /**
   * Send a user action to the backend and get SSE stream back
   * 
   * @param agentId - Agent identifier
   * @param action - User action details
   * @param threadId - Thread ID for conversation context
   * @param runId - Run ID for this execution
   * @param onEvent - Callback for SSE events
   * @param model - Optional model identifier to use for this action
   * @param provider - Optional provider identifier to use for this action
   * @returns Abort controller to cancel the request
   */
  static async sendAction(
    agentId: string,
    action: UserAction,
    threadId: string,
    runId: string,
    onEvent: (event: any) => void,
    model?: string,
    provider?: string
  ): Promise<AbortController> {
    const abortController = new AbortController();
    
    const requestBody: UserActionRequest = {
      userAction: action,
      threadId,
      runId,
      ...(model && { model }),
      ...(provider && { provider })
    };
    
    try {
      console.log('[A2UIUserAction] Sending action:', {
        agentId,
        actionName: action.name,
        surfaceId: action.surfaceId,
        threadId,
        runId,
        model,
        provider
      });
      
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestBody),
        signal: abortController.signal
      });
      
      console.log('[A2UIUserAction] Response status:', response.status);
      
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
      
      console.log('[A2UIUserAction] Starting to read event stream...');
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('[A2UIUserAction] Stream completed');
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
              console.log('[A2UIUserAction] Received event:', event.type);
              onEvent(event);
            } catch (error) {
              console.error('[A2UIUserAction] Error parsing SSE event:', error, 'Data:', data);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('[A2UIUserAction] Request aborted');
      } else {
        console.error('[A2UIUserAction] Error sending action:', error);
        onEvent({
          type: 'ERROR',
          message: error instanceof Error ? error.message : 'Unknown error',
          timestamp: Date.now(),
        });
      }
    }
    
    return abortController;
  }
  
  /**
   * Create a UserAction from component interaction
   * 
   * @param actionName - Name of the action from component definition
   * @param surfaceId - ID of the surface containing the component
   * @param componentId - ID of the component that triggered the action
   * @param context - Resolved context data from data model
   * @returns UserAction object ready to send
   */
  static createUserAction(
    actionName: string,
    surfaceId: string,
    componentId: string,
    context: Record<string, any>
  ): UserAction {
    return {
      name: actionName,
      surfaceId,
      sourceComponentId: componentId,
      timestamp: new Date().toISOString(),
      context
    };
  }
}
