import { AGUIEvent, ConnectionState } from '@/types/agui';

/**
 * AG-UI Client for handling Server-Sent Events (SSE) from backend
 * 
 * This client processes real-time event streams following the AG-UI protocol
 * Events are received through the streaming API response
 */
export class AGUIClient {
  private listeners: Map<string, ((event: AGUIEvent) => void)[]> = new Map();
  private connectionState: ConnectionState = {
    isConnected: false,
    error: null,
    lastEventTime: null,
  };

  /**
   * Process an AG-UI event
   * This is called by the API client when it receives an event from the stream
   */
  processEvent(aguiEvent: AGUIEvent): void {
    try {
      aguiEvent.timestamp = aguiEvent.timestamp || Date.now();
      this.connectionState.lastEventTime = Date.now();
      
      console.log('AGUIClient: Processing event:', aguiEvent.type, aguiEvent);
      
      // Emit to specific event type listeners
      this.emit(aguiEvent.type, aguiEvent);
      // Emit to catch-all listeners
      this.emit('*', aguiEvent);
    } catch (error) {
      console.error('Error processing AG-UI event:', error);
    }
  }

  /**
   * Set connection state
   */
  setConnected(connected: boolean, error: string | null = null): void {
    this.connectionState = {
      isConnected: connected,
      error,
      lastEventTime: Date.now(),
    };
    
    if (connected) {
      this.emit('connection', { 
        type: 'COMPLETE', 
        data: { connected: true }, 
        timestamp: Date.now() 
      });
    } else if (error) {
      this.emit('error', { 
        type: 'ERROR', 
        data: { message: error }, 
        timestamp: Date.now() 
      });
    }
  }

  /**
   * Register an event listener
   * Returns an unsubscribe function
   */
  on(eventType: string, callback: (event: AGUIEvent) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(callback);
    
    // Return unsubscribe function
    return () => this.off(eventType, callback);
  }

  /**
   * Remove an event listener
   */
  off(eventType: string, callback: (event: AGUIEvent) => void): void {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index >= 0) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Emit an event to all registered listeners
   */
  private emit(eventType: string, event: AGUIEvent): void {
    const listeners = this.listeners.get(eventType);
    console.log(`AGUIClient: Emitting ${eventType}, listeners count:`, listeners?.length || 0);
    if (listeners) {
      listeners.forEach(callback => callback(event));
    }
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return { ...this.connectionState };
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
  }
  return clientInstance;
}
