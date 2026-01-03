/**
 * A2UIManager - Manages A2UI component actions and data model interactions
 * 
 * This manager class provides a centralized way to:
 * - Register action callbacks for different surfaces
 * - Handle component actions and route them to registered callbacks
 * - Resolve action context with data model values
 * - Update data model values
 */

import { useA2UIStore } from '@/stores/a2uiStore';
import type { UserAction } from '@/types/a2ui';

type ActionCallback = (action: UserAction) => void;

export class A2UIManager {
  private actionCallbacks: Map<string, ActionCallback> = new Map();

  /**
   * Register an action callback for a specific surface or wildcard
   * @param surfaceId - Surface ID or '*' for wildcard
   * @param callback - Callback to invoke when action occurs
   */
  onAction(surfaceId: string, callback: ActionCallback): void {
    this.actionCallbacks.set(surfaceId, callback);
  }

  /**
   * Handle a component action
   * @param surfaceId - Surface ID where action occurred
   * @param componentId - Component ID that triggered the action
   * @param actionName - Name of the action
   * @param context - Action context (may contain path references)
   */
  handleComponentAction(
    surfaceId: string,
    componentId: string,
    actionName: string,
    context: Record<string, any>
  ): void {
    // Find callback - prefer specific surface over wildcard
    const callback = this.actionCallbacks.get(surfaceId) || this.actionCallbacks.get('*');

    if (!callback) {
      console.warn(
        `[A2UIManager] No action callback registered for surface: ${surfaceId} or wildcard (*)`
      );
      return;
    }

    // Resolve context with data model values
    const resolvedContext = this.resolveActionContext(surfaceId, context);

    // Create UserAction
    const userAction: UserAction = {
      name: actionName,
      surfaceId,
      sourceComponentId: componentId,
      context: resolvedContext,
      timestamp: new Date().toISOString()
    };

    // Invoke callback
    callback(userAction);
  }

  /**
   * Resolve action context by converting path references to actual values
   * @param surfaceId - Surface ID
   * @param context - Raw context with potential path references
   * @returns Resolved context with actual values
   */
  resolveActionContext(surfaceId: string, context: Record<string, any>): Record<string, any> {
    const resolved: Record<string, any> = {};

    for (const [key, value] of Object.entries(context)) {
      // Check if value is a path reference object
      if (value && typeof value === 'object' && 'path' in value && typeof value.path === 'string') {
        // Resolve path from data model
        resolved[key] = this.getValueAtPath(surfaceId, value.path);
      } else {
        // Keep literal value as is
        resolved[key] = value;
      }
    }

    return resolved;
  }

  /**
   * Update a value in the data model at a specific path
   * @param surfaceId - Surface ID
   * @param path - Path to update
   * @param value - New value
   */
  updateDataModelValue(surfaceId: string, path: string, value: any): void {
    const store = useA2UIStore.getState();
    store.setValueAtPath(surfaceId, path, value);
  }

  /**
   * Get a value from the data model at a specific path
   * @param surfaceId - Surface ID
   * @param path - Path to retrieve
   * @returns Value at path or undefined
   */
  getValueAtPath(surfaceId: string, path: string): any {
    const store = useA2UIStore.getState();
    return store.getValueAtPath(surfaceId, path);
  }
}

// Singleton instance
export const a2uiManager = new A2UIManager();
