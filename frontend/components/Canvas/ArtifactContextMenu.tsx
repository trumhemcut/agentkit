"use client";

import { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { MessageCircle } from 'lucide-react';

interface ArtifactContextMenuProps {
  selectedText: string;
  position: { x: number; y: number };
  onChatWithAgent: (text: string) => void;
  onClose: () => void;
}

/**
 * ArtifactContextMenu Component
 * 
 * Custom horizontal context menu that appears when text is selected in the artifact panel.
 * Provides a "Chat with agent" action to discuss the selected text.
 */
export function ArtifactContextMenu({
  selectedText,
  position,
  onChatWithAgent,
  onClose
}: ArtifactContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg p-1 flex items-center gap-1 animate-in fade-in-0 zoom-in-95 duration-200"
      style={{
        top: `${position.y - 40}px`,
        left: `${position.x}px`,
      }}
    >
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onChatWithAgent(selectedText)}
        className="flex items-center gap-2 h-8 px-3 text-sm font-medium hover:bg-blue-50 hover:text-blue-600 transition-colors"
      >
        <MessageCircle className="h-4 w-4" />
        Chat with agent
      </Button>
    </div>
  );
}
