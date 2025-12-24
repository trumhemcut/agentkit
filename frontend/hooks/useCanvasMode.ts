import { useState, useCallback } from 'react';
import { Message, isArtifactMessage } from '@/types/chat';

export interface CanvasMode {
  isActive: boolean;
  currentArtifactMessage: Message | null;
}

export interface UseCanvasModeReturn extends CanvasMode {
  activateCanvas: (message: Message) => void;
  deactivateCanvas: () => void;
  updateCurrentArtifact: (message: Message) => void;
}

/**
 * Hook to manage canvas mode state
 * Canvas mode is activated when an artifact message is detected
 */
export function useCanvasMode(): UseCanvasModeReturn {
  const [isActive, setIsActive] = useState(false);
  const [currentArtifactMessage, setCurrentArtifactMessage] = useState<Message | null>(null);

  const activateCanvas = useCallback((message: Message) => {
    if (!isArtifactMessage(message)) {
      console.warn('Attempted to activate canvas with non-artifact message');
      return;
    }
    
    setIsActive(true);
    setCurrentArtifactMessage(message);
  }, []);

  const deactivateCanvas = useCallback(() => {
    setIsActive(false);
    setCurrentArtifactMessage(null);
  }, []);

  const updateCurrentArtifact = useCallback((message: Message) => {
    if (!isArtifactMessage(message)) {
      console.warn('Attempted to update artifact with non-artifact message');
      return;
    }
    
    setCurrentArtifactMessage(message);
  }, []);

  return {
    isActive,
    currentArtifactMessage,
    activateCanvas,
    deactivateCanvas,
    updateCurrentArtifact,
  };
}
