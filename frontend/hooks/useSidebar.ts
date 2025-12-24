'use client';

import { useState, useEffect } from 'react';

/**
 * Hook to manage sidebar collapse state with localStorage persistence
 */
export function useSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load collapsed state from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('sidebar-collapsed');
    if (stored !== null) {
      setIsCollapsed(stored === 'true');
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage when state changes
  const toggleCollapse = () => {
    setIsCollapsed((prev) => {
      const newValue = !prev;
      localStorage.setItem('sidebar-collapsed', String(newValue));
      return newValue;
    });
  };

  // Set collapsed state directly
  const setCollapsed = (collapsed: boolean) => {
    setIsCollapsed(collapsed);
    localStorage.setItem('sidebar-collapsed', String(collapsed));
  };

  return {
    isCollapsed,
    toggleCollapse,
    setCollapsed,
    isLoaded, // Use this to avoid flash of wrong state on load
  };
}
