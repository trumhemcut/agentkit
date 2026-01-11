'use client';

import { Plus, MessageSquare, PanelLeftClose, PanelLeftOpen, Search, Sparkles, X, Settings } from 'lucide-react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Thread } from '@/types/database';
import { cn } from '@/lib/utils';
import { ChatHistory } from './ChatHistory';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { useHorizontalSwipe } from '@/hooks/useSwipeGesture';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface SidebarProps {
  threads: Thread[];
  currentThreadId: string | null;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onNewChat: () => void;
  onSelectThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
  // Mobile drawer props
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

/**
 * Sidebar component
 * 
 * Displays thread list with new chat button, collapse functionality, and thread management.
 * On mobile (<768px), sidebar becomes a drawer that slides in from the left.
 */
export function Sidebar({
  threads,
  currentThreadId,
  isCollapsed,
  onToggleCollapse,
  onNewChat,
  onSelectThread,
  onDeleteThread,
  isMobileOpen = false,
  onCloseMobile,
}: SidebarProps) {
  const isMobile = useIsMobile();
  const router = useRouter();

  // Swipe gesture for mobile drawer
  const swipeHandlers = useHorizontalSwipe(
    () => {
      // Swipe left to close
      if (isMobile && isMobileOpen && onCloseMobile) {
        onCloseMobile();
      }
    },
    undefined, // No swipe right handler (opening handled by edge swipe in parent)
    { threshold: 75 }
  );

  // Close drawer on escape key
  useEffect(() => {
    if (!isMobile || !isMobileOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && onCloseMobile) {
        onCloseMobile();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isMobile, isMobileOpen, onCloseMobile]);

  // Prevent body scroll when mobile drawer is open
  useEffect(() => {
    if (isMobile && isMobileOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isMobile, isMobileOpen]);

  const handleThreadSelect = (threadId: string) => {
    onSelectThread(threadId);
    // Auto-close mobile drawer after selection
    if (isMobile && onCloseMobile) {
      onCloseMobile();
    }
  };

  const handleNewChat = () => {
    onNewChat();
    // Auto-close mobile drawer after action
    if (isMobile && onCloseMobile) {
      onCloseMobile();
    }
  };

  // Mobile: render as overlay drawer
  if (isMobile) {
    return (
      <>
        {/* Backdrop */}
        {isMobileOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/50 transition-opacity"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
        )}

        {/* Mobile Drawer */}
        <aside
          {...swipeHandlers}
          className={cn(
            "fixed inset-y-0 left-0 z-50 flex h-screen w-64 flex-col transition-transform duration-300 ease-in-out",
            "text-gray-900 bg-[#F7F7F8]",
            isMobileOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          {/* Header with Logo and Close Button */}
          <div className="flex h-16 items-center justify-between px-3 shrink-0">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg">
                <Image
                  src="/logo.svg"
                  alt="AgentKit Logo"
                  width={32}
                  height={32}
                  priority
                  className="h-8 w-8"
                />
              </div>
              <span className="font-semibold text-gray-900">AgentKit</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onCloseMobile}
              className="h-8 w-8 shrink-0"
              title="Close sidebar"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* New Chat Button */}
          <div className="p-2 shrink-0">
            <Button
              onClick={handleNewChat}
              variant="ghost"
              className="w-full justify-start gap-2 h-10 px-3 hover:bg-gray-200 text-gray-900"
            >
              <Plus className="h-4 w-4" />
              <span className="font-medium">New chat</span>
            </Button>
          </div>

          <div className="px-4 py-2 shrink-0">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Your chats
            </p>
          </div>

          {/* Thread List */}
          <div className="flex-1 min-h-0 overflow-hidden">
            {threads.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center px-4 h-full">
                <MessageSquare className="mb-2 h-8 w-8 text-gray-400" />
                <p className="text-sm text-gray-600">No chats yet</p>
                <p className="text-xs text-gray-500">Start a new conversation</p>
              </div>
            ) : (
              <div className="h-full overflow-y-auto overflow-x-hidden scrollbar-thin">
                <ChatHistory
                  threads={threads}
                  currentThreadId={currentThreadId}
                  isCollapsed={false}
                  onSelectThread={handleThreadSelect}
                  onDeleteThread={onDeleteThread}
                />
              </div>
            )}
          </div>

          {/* Settings Button */}
          <div className="p-2 shrink-0 border-t border-gray-200">
            <Button
              onClick={() => {
                router.push('/settings');
                if (onCloseMobile) onCloseMobile();
              }}
              variant="ghost"
              className="w-full justify-start gap-2 h-10 px-3 hover:bg-gray-200 text-gray-900"
            >
              <Settings className="h-4 w-4" />
              <span className="font-medium">Settings</span>
            </Button>
          </div>
        </aside>
      </>
    );
  }

  // Desktop: render as static sidebar
  return (
    <aside
      className={cn(
        "flex h-screen flex-col transition-all duration-300 ease-in-out",
        isCollapsed ? "w-16" : "w-64",
        "text-gray-900"
      )}
      style={{ backgroundColor: '#F7F7F8' }}
    >
      {/* Header with Logo and Collapse Toggle */}
      <div className={cn(
        "flex h-16 items-center shrink-0 group",
        isCollapsed ? "flex-col justify-center gap-2 px-2 relative" : "justify-between px-3"
      )}>
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg">
              <Image
                src="/logo.svg"
                alt="AgentKit Logo"
                width={32}
                height={32}
                priority
                className="h-8 w-8"
              />
            </div>
            <span className="font-semibold text-gray-900">AgentKit</span>
          </div>
        )}
        {isCollapsed && (
          <>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg group-hover:opacity-0 transition-opacity">
              <Image
                src="/logo.svg"
                alt="AgentKit Logo"
                width={40}
                height={40}
                priority
                className="h-10 w-10"
              />
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleCollapse}
              className="absolute inset-0 w-full h-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
              title="Expand sidebar"
            >
              <PanelLeftOpen className="h-5 w-5" />
            </Button>
          </>
        )}
        {!isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
            className="h-8 w-8 shrink-0"
            title="Collapse sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* New Chat Button */}
      <div className="p-2 shrink-0">
        {!isCollapsed ? (
          <Button
            onClick={onNewChat}
            variant="ghost"
            className="w-full justify-start gap-2 h-10 px-3 hover:bg-gray-200 text-gray-900"
          >
            <Plus className="h-4 w-4" />
            <span className="font-medium">New chat</span>
          </Button>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Button
              onClick={onNewChat}
              variant="ghost"
              size="icon"
              className="size-10 hover:bg-gray-200"
              title="New Chat"
            >
              <Plus className="size-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-10 hover:bg-gray-200"
              title="Search"
            >
              <Search className="size-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-10 hover:bg-gray-200"
              title="Discover"
            >
              <Sparkles className="size-5" />
            </Button>
          </div>
        )}
      </div>

      {!isCollapsed && (
        <>
          <div className="px-4 py-2 shrink-0">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Your chats
            </p>
          </div>
        </>
      )}

      {/* Thread List - Hidden when collapsed */}
      {!isCollapsed && (
        <div className="flex-1 min-h-0 overflow-hidden">
          {threads.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center px-4 h-full">
              <MessageSquare className="mb-2 h-8 w-8 text-gray-400" />
              <p className="text-sm text-gray-600">No chats yet</p>
              <p className="text-xs text-gray-500">Start a new conversation</p>
            </div>
          ) : (
            <div className="h-full overflow-y-auto overflow-x-hidden scrollbar-thin">
              <ChatHistory
                threads={threads}
                currentThreadId={currentThreadId}
                isCollapsed={isCollapsed}
                onSelectThread={onSelectThread}
                onDeleteThread={onDeleteThread}
              />
            </div>
          )}
        </div>
      )}

      {/* Settings Button */}
      <div className="p-2 shrink-0 border-t border-gray-200">
        {!isCollapsed ? (
          <Button
            onClick={() => router.push('/settings')}
            variant="ghost"
            className="w-full justify-start gap-2 h-10 px-3 hover:bg-gray-200 text-gray-900"
          >
            <Settings className="h-4 w-4" />
            <span className="font-medium">Settings</span>
          </Button>
        ) : (
          <Button
            onClick={() => router.push('/settings')}
            variant="ghost"
            size="icon"
            className="size-10 hover:bg-gray-200"
            title="Settings"
          >
            <Settings className="size-5" />
          </Button>
        )}
      </div>
    </aside>
  );
}
