'use client';

import { useState, useCallback, useRef } from 'react';
import { AGUIEvent } from '@/types/agui';
import { getAGUIClient } from '@/services/agui-client';

/**
 * Hook for AG-UI integration
 * 
 * Provides access to the AG-UI client for processing real-time events
 */
export function useAGUI() {
  const [isConnected, setIsConnected] = useState(false);
  const [currentEvent, setCurrentEvent] = useState<AGUIEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const clientRef = useRef(getAGUIClient());

  /**
   * Set connection status
   */
  const setConnectionState = useCallback((connected: boolean, errorMsg: string | null = null) => {
    setIsConnected(connected);
    setError(errorMsg);
    clientRef.current.setConnected(connected, errorMsg);
  }, []);

  /**
   * Register a custom event listener
   * Returns an unsubscribe function
   */
  const on = useCallback((eventType: string, callback: (event: AGUIEvent) => void) => {
    return clientRef.current.on(eventType, callback);
  }, []);

  /**
   * Get the AG-UI client instance for direct access
   */
  const getClient = useCallback(() => {
    return clientRef.current;
  }, []);

  return {
    isConnected,
    currentEvent,
    error,
    on,
    getClient,
    setConnectionState,
  };
}
