/**
 * A2UI Manager
 * 
 * Central manager for A2UI component actions and data model interactions.
 * Provides integration between UI components and the A2UI store.
 */

import { useA2UIStore } from '@/stores/a2uiStore';
import { resolvePath } from '@/types/a2ui';
import type { UserAction } from '@/types/a2ui';

type ActionCallback = (action: UserAction) => void;

class A2UIManager {
  private actionCallbacks: Map<string, Set<ActionCallback>> = new Map();

  /**
   * Register a callback for actions on a specific surface or all surfaces
   * @param surfaceId - Surface ID or '*' for wildcard (all surfaces)
   * @param callback - Function to call when action occurs
   */
  onAction(surfaceId: string, callback: ActionCallback): void {
    if (!this.actionCallbacks.has(surfaceId)) {
      this.actionCallbacks.set(surfaceId, new Set());
    }
    this.actionCallbacks.get(surfaceId)!.add(callback);
  }

  /**
   * Remove a callback for a specific surface
   * @param surfaceId - Surface ID or '*' for wildcard
   * @param callback - Callback function to remove
   */
  offAction(surfaceId: string, callback: ActionCallback): void {
    const callbacks = this.actionCallbacks.get(surfaceId);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.actionCallbacks.delete(surfaceId);
      }
    }
  }

  /**
   * Handle a component action - resolves context and triggers callbacks
   * @param surfaceId - ID of the surface containing the component
   * @param componentId - ID of the component that triggered the action
   * @param actionName - Name of the action
   * @param context - Context data (may contain path references)
   */
  handleComponentAction(
    surfaceId: string,
    componentId: string,
    actionName: string,
    context: Record<string, any>
  ): void {
    // Resolve context paths to actual values
    const resolvedContext = this.resolveActionContext(surfaceId, context);

    // Create UserAction
    const action: UserAction = {
      name: actionName,
      surfaceId,
      sourceComponentId: componentId,
      timestamp: new Date().toISOString(),
      context: resolvedContext
    };

    // Trigger callbacks for this specific surface
    const surfaceCallbacks = this.actionCallbacks.get(surfaceId);
    if (surfaceCallbacks) {
      surfaceCallbacks.forEach(callback => callback(action));
    }

    // Trigger wildcard callbacks
    const wildcardCallbacks = this.actionCallbacks.get('*');
    if (wildcardCallbacks) {
      wildcardCallbacks.forEach(callback => callback(action));
    }
  }

  /**
   * Resolve action context by converting path references to actual values
   * @param surfaceId - Surface ID to get data model from
   * @param context - Context object that may contain path references
   * @returns Resolved context with actual values
   */
  resolveActionContext(
    surfaceId: string,
    context: Record<string, any>
  ): Record<string, any> {
    const surface = useA2UIStore.getState().getSurface(surfaceId);
    if (!surface) {
      console.warn(`[A2UIManager] Surface not found: ${surfaceId}`);
      return context;
    }

    const resolved: Record<string, any> = {};

    for (const [key, value] of Object.entries(context)) {
      // Check if value is an object with a path property
      if (value && typeof value === 'object' && 'path' in value) {
        // Resolve the path from data model
        resolved[key] = resolvePath(surface.dataModel, value.path);
      } else {
        // Use value as-is
        resolved[key] = value;
      }
    }

    return resolved;
  }

  /**
   * Get value from data model at a specific path
   * @param surfaceId - Surface ID
   * @param path - JSON Pointer path
   * @returns Value at path or undefined
   */
  getValueAtPath(surfaceId: string, path: string): any {
    return useA2UIStore.getState().getValueAtPath(surfaceId, path);
  }

  /**
   * Update value in data model at a specific path
   * @param surfaceId - Surface ID
   * @param path - JSON Pointer path
   * @param value - New value to set
   */
  updateDataModelValue(surfaceId: string, path: string, value: any): void {
    useA2UIStore.getState().setValueAtPath(surfaceId, path, value);
  }
}

// Export singleton instance
export const a2uiManager = new A2UIManager();
