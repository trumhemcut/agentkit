'use client';

import { MessageSquare, Layout } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useHorizontalSwipe } from '@/hooks/useSwipeGesture';

export type MobileTab = 'chat' | 'canvas';

interface MobileTabNavigationProps {
  activeTab: MobileTab;
  onTabChange: (tab: MobileTab) => void;
  showCanvasBadge?: boolean;
}

/**
 * Mobile tab navigation component for switching between Chat and Canvas views
 * Only shown on mobile devices (<768px)
 */
export function MobileTabNavigation({
  activeTab,
  onTabChange,
  showCanvasBadge = false,
}: MobileTabNavigationProps) {
  // Swipe gesture for tab switching
  const swipeHandlers = useHorizontalSwipe(
    () => {
      // Swipe left: Chat → Canvas
      if (activeTab === 'chat') {
        onTabChange('canvas');
      }
    },
    () => {
      // Swipe right: Canvas → Chat
      if (activeTab === 'canvas') {
        onTabChange('chat');
      }
    },
    { threshold: 75 }
  );

  return (
    <div
      {...swipeHandlers}
      className="flex items-center justify-around border-b border-border bg-background h-12 md:hidden"
    >
      {/* Chat Tab */}
      <button
        onClick={() => onTabChange('chat')}
        className={cn(
          "flex flex-1 items-center justify-center gap-2 h-full relative transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          activeTab === 'chat'
            ? "text-foreground border-b-2 border-primary"
            : "text-muted-foreground hover:text-foreground"
        )}
        aria-current={activeTab === 'chat' ? 'page' : undefined}
      >
        <MessageSquare className="h-5 w-5" />
        <span className="font-medium text-sm">Chat</span>
      </button>

      {/* Canvas Tab */}
      <button
        onClick={() => onTabChange('canvas')}
        className={cn(
          "flex flex-1 items-center justify-center gap-2 h-full relative transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          activeTab === 'canvas'
            ? "text-foreground border-b-2 border-primary"
            : "text-muted-foreground hover:text-foreground"
        )}
        aria-current={activeTab === 'canvas' ? 'page' : undefined}
      >
        <Layout className="h-5 w-5" />
        <span className="font-medium text-sm">Canvas</span>
        {/* Notification badge */}
        {showCanvasBadge && activeTab !== 'canvas' && (
          <span className="absolute top-2 right-1/4 h-2 w-2 rounded-full bg-primary animate-pulse" />
        )}
      </button>
    </div>
  );
}
