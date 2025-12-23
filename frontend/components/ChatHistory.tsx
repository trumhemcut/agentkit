'use client';

import { MoreVertical, Trash2, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Thread } from '@/types/chat';
import { cn } from '@/lib/utils';

interface ChatHistoryProps {
  threads: Thread[];
  currentThreadId: string | null;
  isCollapsed: boolean;
  onSelectThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
}

interface ChatHistoryItemProps {
  thread: Thread;
  isActive: boolean;
  isCollapsed: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

function ChatHistoryItem({
  thread,
  isActive,
  isCollapsed,
  onSelect,
  onDelete,
}: ChatHistoryItemProps) {
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div
      className={cn(
        "group relative flex items-center gap-2 rounded-lg px-2 py-1.5 cursor-pointer transition-colors",
        "hover:bg-gray-200",
        isActive && "bg-gray-200"
      )}
      onClick={onSelect}
      title={isCollapsed ? thread.title : undefined}
    >
      {!isCollapsed && (
        <>
          <div className="flex-1 overflow-hidden min-w-0">
            <p className="truncate text-sm">{thread.title}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                className="text-destructive cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </>
      )}
    </div>
  );
}

/**
 * Chat History component
 * 
 * Displays thread list in sidebar with delete functionality
 */
export function ChatHistory({
  threads,
  currentThreadId,
  isCollapsed,
  onSelectThread,
  onDeleteThread,
}: ChatHistoryProps) {
  return (
    <div className="space-y-1 p-2">
      {threads.map((thread) => (
        <ChatHistoryItem
          key={thread.id}
          thread={thread}
          isActive={currentThreadId === thread.id}
          isCollapsed={isCollapsed}
          onSelect={() => onSelectThread(thread.id)}
          onDelete={() => onDeleteThread(thread.id)}
        />
      ))}
    </div>
  );
}
