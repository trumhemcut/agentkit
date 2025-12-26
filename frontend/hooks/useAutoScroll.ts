'use client';

import { useRef, useEffect, useState, useCallback, useLayoutEffect } from 'react';

interface UseAutoScrollOptions {
  /**
   * Whether this is the initial load (no auto-scroll on initial load)
   */
  isInitialLoad?: boolean;
  /**
   * Distance from bottom (in pixels) to consider "at bottom"
   */
  scrollThreshold?: number;
}

/**
 * Hook to manage auto-scroll behavior for chat messages
 * 
 * Features:
 * - Auto-scrolls when user is near bottom and new messages arrive
 * - Preserves scroll position when user manually scrolls up
 * - Skips auto-scroll on initial thread history load
 * - Provides scroll-to-bottom function for manual control
 */
export function useAutoScroll(dependencies: any[], options: UseAutoScrollOptions = {}) {
  const { isInitialLoad = false, scrollThreshold = 100 } = options;
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const previousScrollHeight = useRef(0);
  const isInitialLoadRef = useRef(isInitialLoad);

  // Update initial load flag
  useEffect(() => {
    isInitialLoadRef.current = isInitialLoad;
  }, [isInitialLoad]);

  /**
   * Check if scroll position is near bottom
   */
  const isNearBottom = useCallback(() => {
    if (!scrollRef.current) return false;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    
    return distanceFromBottom < scrollThreshold;
  }, [scrollThreshold]);

  /**
   * Handle scroll events to detect user manual scrolling
   */
  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return;
    
    // Mark user as scrolling
    setIsUserScrolling(true);
    
    // Clear existing timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    
    // Reset user scrolling flag after 150ms of no scrolling
    scrollTimeoutRef.current = setTimeout(() => {
      setIsUserScrolling(false);
    }, 150);
    
    // Update auto-scroll flag based on position
    const nearBottom = isNearBottom();
    setShouldAutoScroll(nearBottom);
  }, [isNearBottom]);

  /**
   * Scroll to bottom of container
   */
  const scrollToBottom = useCallback((smooth = true) => {
    if (!scrollRef.current) return;
    
    scrollRef.current.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    });
    
    setShouldAutoScroll(true);
  }, []);

  /**
   * Auto-scroll on new messages (dependencies change)
   */
  useEffect(() => {
    if (!scrollRef.current) return;
    
    const currentScrollHeight = scrollRef.current.scrollHeight;
    const hasNewContent = currentScrollHeight !== previousScrollHeight.current;
    previousScrollHeight.current = currentScrollHeight;

    // Skip on initial load
    if (isInitialLoadRef.current) {
      console.log('[useAutoScroll] Skipping auto-scroll on initial load');
      return;
    }

    // Skip if no new content
    if (!hasNewContent) {
      console.log('[useAutoScroll] Skipping auto-scroll - no new content');
      return;
    }

    // Only auto-scroll if user is near bottom and not actively scrolling
    if (shouldAutoScroll && !isUserScrolling) {
      console.log('[useAutoScroll] Auto-scrolling to bottom');
      requestAnimationFrame(() => {
        scrollToBottom(true);
      });
    } else {
      console.log('[useAutoScroll] Skipping auto-scroll - shouldAutoScroll:', shouldAutoScroll, 'isUserScrolling:', isUserScrolling);
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // Re-check scroll position after layout changes (e.g., canvas mode toggle)
  useLayoutEffect(() => {
    if (!scrollRef.current || isInitialLoadRef.current) return;
    
    // After layout changes, re-evaluate if we're near bottom
    const nearBottom = isNearBottom();
    if (nearBottom !== shouldAutoScroll) {
      console.log('[useAutoScroll] Layout changed, updating shouldAutoScroll:', nearBottom);
      setShouldAutoScroll(nearBottom);
    }
  });

  return {
    scrollRef,
    handleScroll,
    scrollToBottom,
    shouldAutoScroll,
    isNearBottom,
  };
}
