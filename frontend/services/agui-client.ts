import { AGUIEvent, ConnectionState, EventType } from '@/types/agui';

/**
 * AG-UI Client for handling Server-Sent Events (SSE) from backend
 * 
 * This client processes real-time event streams following the AG-UI protocol.
 * It's compatible with the official ag-ui-protocol from the backend.
 * 
 * Events are received through the streaming API response and processed by this client.
 * The client maintains listeners for specific event types and emits events to subscribers.
 * 
 * @see https://docs.ag-ui.com for AG-UI protocol documentation
 */
export class AGUIClient {
  private listeners: Map<string, ((event: AGUIEvent) => void)[]> = new Map();
  private connectionState: ConnectionState = {
    isConnected: false,
    error: null,
    lastEventTime: null,
  };

  /**
   * Process an AG-UI event from the backend stream
   * This is called by the API client when it receives an event from the SSE stream
   * 
   * @param aguiEvent - The event received from the backend
   */
  processEvent(aguiEvent: AGUIEvent): void {
    try {
      // Add timestamp if not present
      aguiEvent.timestamp = aguiEvent.timestamp || Date.now();
      this.connectionState.lastEventTime = Date.now();
      
      console.log('[AGUI] Processing event:', aguiEvent.type, aguiEvent);
      
      // Emit to specific event type listeners
      this.emit(aguiEvent.type, aguiEvent);
      
      // Emit to catch-all listeners
      this.emit('*', aguiEvent);
    } catch (error) {
      console.error('[AGUI] Error processing event:', error);
      this.emit('error', {
        type: EventType.ERROR,
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      });
    }
  }

  /**
   * Set connection state
   * 
   * @param connected - Whether the connection is active
   * @param error - Optional error message
   */
  setConnected(connected: boolean, error: string | null = null): void {
    this.connectionState = {
      isConnected: connected,
      error,
      lastEventTime: Date.now(),
    };
    
    console.log('[AGUI] Connection state changed:', { connected, error });
    
    if (connected) {
      this.emit('connection', { 
        type: EventType.COMPLETE, 
        timestamp: Date.now() 
      });
    } else if (error) {
      this.emit('error', { 
        type: EventType.ERROR, 
        message: error,
        timestamp: Date.now() 
      });
    }
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return { ...this.connectionState };
  }

  /**
   * Register an event listener
   * 
   * @param eventType - The event type to listen for (use '*' for all events)
   * @param callback - Function to call when event is received
   * @returns Unsubscribe function
   */
  on(eventType: string, callback: (event: AGUIEvent) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(callback);
    
    console.log(`[AGUI] Registered listener for: ${eventType}`);
    
    // Return unsubscribe function
    return () => this.off(eventType, callback);
  }

  /**
   * Remove an event listener
   * 
   * @param eventType - The event type to unsubscribe from
   * @param callback - The callback function to remove
   */
  off(eventType: string, callback: (event: AGUIEvent) => void): void {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index >= 0) {
        listeners.splice(index, 1);
        console.log(`[AGUI] Removed listener for: ${eventType}`);
      }
    }
  }

  /**
   * Emit an event to all registered listeners
   * 
   * @param eventType - The type of event to emit
/**
   * Emit an event to all registered listeners
   * 
   * @param eventType - The type of event to emit
   * @param event - The event data
   */
  private emit(eventType: string, event: AGUIEvent): void {
    const listeners = this.listeners.get(eventType);
    if (listeners && listeners.length > 0) {
      console.log(`[AGUI] Emitting ${eventType} to ${listeners.length} listener(s)`);
      listeners.forEach(callback => {
        try {
          callback(event);
        } catch (error) {
          console.error(`[AGUI] Error in listener for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Clear all event listeners
   */
  clearListeners(): void {
    this.listeners.clear();
    console.log('[AGUI] Cleared all listeners');
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState.isConnected;
  }
}

// Singleton instance
let clientInstance: AGUIClient | null = null;

/**
 * Get the singleton AG-UI client instance
 */
export function getAGUIClient(): AGUIClient {
  if (!clientInstance) {
    clientInstance = new AGUIClient();
    console.log('[AGUI] Created new client instance');
  }
  return clientInstance;
}
