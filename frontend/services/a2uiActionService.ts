/**
 * A2UI User Action Service
 * 
 * Handles sending user interaction events from A2UI components back to the backend.
 * This allows the backend agent to respond to user actions like button clicks,
 * checkbox changes, and input updates.
 */

import type { UserAction } from '@/types/a2ui';

export class A2UIActionService {
  private baseUrl: string;
  
  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  /**
   * Send a user action to the backend
   * 
   * @param surfaceId - The surface ID where the action occurred
   * @param actionName - Name of the action (e.g., "button_clicked", "checkbox_changed")
   * @param context - Additional context data for the action
   * @param threadId - Optional thread ID to associate the action with
   */
  async sendUserAction(
    surfaceId: string,
    actionName: string,
    context: Record<string, any>,
    threadId?: string
  ): Promise<void> {
    const userAction: UserAction = {
      type: 'userAction',
      surfaceId,
      actionName,
      context: {
        ...context,
        threadId,
        timestamp: new Date().toISOString()
      }
    };
    
    try {
      const response = await fetch(`${this.baseUrl}/api/a2ui/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userAction),
      });
      
      if (!response.ok) {
        console.error('[A2UIActionService] Failed to send user action:', response.statusText);
      }
    } catch (error) {
      console.error('[A2UIActionService] Error sending user action:', error);
    }
  }
  
  /**
   * Create a callback function for use in A2UI components
   * 
   * @param threadId - The current thread ID
   * @returns Callback function that sends user actions
   */
  createActionCallback(threadId?: string) {
    return (actionName: string, context: Record<string, any>) => {
      const surfaceId = context.surfaceId;
      if (!surfaceId) {
        console.warn('[A2UIActionService] No surfaceId in context, skipping action');
        return;
      }
      
      this.sendUserAction(surfaceId, actionName, context, threadId);
    };
  }
}

// Singleton instance
export const a2uiActionService = new A2UIActionService();
