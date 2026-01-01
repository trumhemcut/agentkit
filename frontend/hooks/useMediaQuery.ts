'use client';

import { useState, useEffect } from 'react';

/**
 * Standard breakpoints for responsive design
 * sm: 640px  - Small devices (mobile landscape)
 * md: 768px  - Medium devices (tablets)
 * lg: 1024px - Large devices (desktops)
 * xl: 1280px - Extra large devices
 */
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const;

/**
 * Hook to detect if a media query matches
 * @param query - Media query string (e.g., "(min-width: 768px)")
 * @returns boolean indicating if the media query matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handler);
      return () => mediaQuery.removeListener(handler);
    }
  }, [query]);

  // Return false on server-side to avoid hydration mismatch
  if (!mounted) {
    return false;
  }

  return matches;
}

/**
 * Helper hook to detect if viewport is mobile size (< 768px)
 */
export function useIsMobile(): boolean {
  return useMediaQuery(`(max-width: ${BREAKPOINTS.md - 1}px)`);
}

/**
 * Helper hook to detect if viewport is tablet size (>= 768px and < 1024px)
 */
export function useIsTablet(): boolean {
  const isAboveMobile = useMediaQuery(`(min-width: ${BREAKPOINTS.md}px)`);
  const isBelowDesktop = useMediaQuery(`(max-width: ${BREAKPOINTS.lg - 1}px)`);
  return isAboveMobile && isBelowDesktop;
}

/**
 * Helper hook to detect if viewport is desktop size (>= 1024px)
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(`(min-width: ${BREAKPOINTS.lg}px)`);
}

/**
 * Hook to get all breakpoint states at once
 */
export function useBreakpoints() {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();

  return {
    isMobile,
    isTablet,
    isDesktop,
    // Convenience flags
    isMobileOrTablet: isMobile || isTablet,
    isTabletOrDesktop: isTablet || isDesktop,
  };
}
