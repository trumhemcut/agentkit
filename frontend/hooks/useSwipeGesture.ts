'use client';

import { useRef, useCallback, TouchEvent } from 'react';

export type SwipeDirection = 'left' | 'right' | 'up' | 'down';

export interface SwipeGestureConfig {
  /** Minimum distance (in pixels) to trigger a swipe */
  threshold?: number;
  /** Minimum velocity (pixels per millisecond) to trigger a swipe */
  velocityThreshold?: number;
  /** Callback when swipe is detected */
  onSwipe?: (direction: SwipeDirection, distance: number, velocity: number) => void;
  /** Callback during swipe movement */
  onSwiping?: (deltaX: number, deltaY: number) => void;
  /** Callback when swipe starts */
  onSwipeStart?: (x: number, y: number) => void;
  /** Callback when swipe ends */
  onSwipeEnd?: () => void;
}

interface TouchState {
  startX: number;
  startY: number;
  startTime: number;
  currentX: number;
  currentY: number;
  isSwiping: boolean;
}

/**
 * Hook to detect and handle swipe gestures
 * @param config - Configuration object for swipe detection
 * @returns Touch event handlers to attach to an element
 */
export function useSwipeGesture(config: SwipeGestureConfig = {}) {
  const {
    threshold = 50,
    velocityThreshold = 0.3,
    onSwipe,
    onSwiping,
    onSwipeStart,
    onSwipeEnd,
  } = config;

  const touchState = useRef<TouchState>({
    startX: 0,
    startY: 0,
    startTime: 0,
    currentX: 0,
    currentY: 0,
    isSwiping: false,
  });

  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      const touch = e.touches[0];
      touchState.current = {
        startX: touch.clientX,
        startY: touch.clientY,
        startTime: Date.now(),
        currentX: touch.clientX,
        currentY: touch.clientY,
        isSwiping: true,
      };
      onSwipeStart?.(touch.clientX, touch.clientY);
    },
    [onSwipeStart]
  );

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!touchState.current.isSwiping) return;

      const touch = e.touches[0];
      touchState.current.currentX = touch.clientX;
      touchState.current.currentY = touch.clientY;

      const deltaX = touch.clientX - touchState.current.startX;
      const deltaY = touch.clientY - touchState.current.startY;

      onSwiping?.(deltaX, deltaY);
    },
    [onSwiping]
  );

  const handleTouchEnd = useCallback(() => {
    if (!touchState.current.isSwiping) return;

    const deltaX = touchState.current.currentX - touchState.current.startX;
    const deltaY = touchState.current.currentY - touchState.current.startY;
    const deltaTime = Date.now() - touchState.current.startTime;

    // Calculate distance and velocity
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    const velocity = distance / deltaTime;

    // Determine swipe direction based on dominant axis
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    let direction: SwipeDirection | null = null;

    // Only trigger if meets threshold requirements
    if (distance >= threshold && velocity >= velocityThreshold) {
      if (absDeltaX > absDeltaY) {
        // Horizontal swipe
        direction = deltaX > 0 ? 'right' : 'left';
      } else {
        // Vertical swipe
        direction = deltaY > 0 ? 'down' : 'up';
      }
    }

    // Reset state
    touchState.current.isSwiping = false;
    onSwipeEnd?.();

    // Trigger callback if valid swipe detected
    if (direction && onSwipe) {
      onSwipe(direction, distance, velocity);
    }
  }, [threshold, velocityThreshold, onSwipe, onSwipeEnd]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
  };
}

/**
 * Specialized hook for horizontal swipes only (left/right)
 */
export function useHorizontalSwipe(
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void,
  options: Omit<SwipeGestureConfig, 'onSwipe'> = {}
) {
  return useSwipeGesture({
    ...options,
    onSwipe: (direction) => {
      if (direction === 'left' && onSwipeLeft) {
        onSwipeLeft();
      } else if (direction === 'right' && onSwipeRight) {
        onSwipeRight();
      }
    },
  });
}

/**
 * Specialized hook for vertical swipes only (up/down)
 */
export function useVerticalSwipe(
  onSwipeUp?: () => void,
  onSwipeDown?: () => void,
  options: Omit<SwipeGestureConfig, 'onSwipe'> = {}
) {
  return useSwipeGesture({
    ...options,
    onSwipe: (direction) => {
      if (direction === 'up' && onSwipeUp) {
        onSwipeUp();
      } else if (direction === 'down' && onSwipeDown) {
        onSwipeDown();
      }
    },
  });
}
