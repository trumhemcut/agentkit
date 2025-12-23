'use client';

import { Plus, MessageSquare, PanelLeftClose, PanelLeftOpen, Bot, Search, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Thread } from '@/types/chat';
import { cn } from '@/lib/utils';
import { ChatHistory } from './ChatHistory';

interface SidebarProps {
  threads: Thread[];
  currentThreadId: string | null;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onNewChat: () => void;
  onSelectThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
}

/**
 * Sidebar component
 * 
 * Displays thread list with new chat button, collapse functionality, and thread management
 */
export function Sidebar({
  threads,
  currentThreadId,
  isCollapsed,
  onToggleCollapse,
  onNewChat,
  onSelectThread,
  onDeleteThread,
}: SidebarProps) {
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
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-900 text-white">
              <Bot className="h-5 w-5" />
            </div>
            <span className="font-semibold text-gray-900">AgentKit</span>
          </div>
        )}
        {isCollapsed && (
          <>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-900 text-white group-hover:opacity-0 transition-opacity">
              <Bot className="h-5 w-5" />
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

      <Separator />

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
          <Button 
            onClick={onNewChat} 
            variant="ghost"
            size="icon" 
            className="w-10 h-10 mx-auto hover:bg-gray-200"
            title="New Chat"
          >
            <Plus className="h-5 w-5" />
          </Button>
        )}
      </div>

      {isCollapsed && (
        <div className="flex flex-col items-center gap-2 p-2 shrink-0">
          <Button 
            variant="ghost"
            size="icon" 
            className="w-10 h-10 hover:bg-gray-200"
            title="Search"
          >
            <Search className="h-5 w-5" />
          </Button>
          <Button 
            variant="ghost"
            size="icon" 
            className="w-10 h-10 hover:bg-gray-200"
            title="Discover"
          >
            <Sparkles className="h-5 w-5" />
          </Button>
        </div>
      )}

      {!isCollapsed && (
        <>
          <Separator />
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
    </aside>
  );
}
