'use client';

import { useState, KeyboardEvent, useRef, forwardRef, useImperativeHandle } from 'react';
import { Send, Plus, Wrench, Upload, Image, Code, FileText, Square } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onStopStreaming?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
}

export interface ChatInputRef {
  focus: () => void;
}

/**
 * Chat Input component
 * 
 * Message input box with action buttons and send button
 */
export const ChatInput = forwardRef<ChatInputRef, ChatInputProps>(function ChatInput({ 
  onSendMessage,
  onStopStreaming,
  disabled = false,
  isStreaming = false,
  placeholder = "Type your message..."
}, ref) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isMobile = useIsMobile();

  useImperativeHandle(ref, () => ({
    focus: () => {
      textareaRef.current?.focus();
    }
  }));

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
    }
  };

  const handleStop = () => {
    if (onStopStreaming) {
      onStopStreaming();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      
      // If streaming, stop and send new message
      if (isStreaming) {
        handleStop();
        // Wait briefly then send
        setTimeout(() => handleSend(), 150);
      } else {
        handleSend();
      }
    }
  };

  const handleFileUpload = () => {
    // Placeholder for future file upload functionality
    console.log('File upload clicked (placeholder)');
  };

  const handleTools = () => {
    // Placeholder for future tools menu functionality
    console.log('Tools clicked (placeholder)');
  };

  const handleUploadFile = () => {
    console.log('Upload file clicked');
    // TODO: Implement file upload
  };

  const handleCreateImage = () => {
    console.log('Create image clicked');
    // TODO: Implement image creation
  };

  const handleGenerateCode = () => {
    console.log('Generate code clicked');
    // TODO: Implement code generation
  };

  const handleAnalyzeDocument = () => {
    console.log('Analyze document clicked');
    // TODO: Implement document analysis
  };

  return (
    <div className={cn(
      "bg-background",
      // Mobile: full width with smaller padding
      // Desktop: constrained width and centered
      isMobile ? "p-3 w-full" : "p-4 max-w-[800px] mx-auto w-full"
    )}>
      <div className="relative">
        {/* Textarea */}
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "resize-none w-full pr-3 rounded-3xl shadow-md hover:shadow-lg transition-shadow",
            isMobile ? "min-h-[50px] max-h-[85px] pb-11 pl-3 pt-3" : "min-h-[60px] max-h-[120px] pb-11 pl-4 pt-3"
          )}
          rows={isMobile ? 1 : 2}
        />
        
        {/* Action buttons container - positioned at bottom of textarea */}
        <div className={cn(
          "absolute left-0 right-0 flex items-center justify-between",
          isMobile ? "bottom-1.5 px-2" : "bottom-2 px-3"
        )}>
          <div className="flex items-center gap-1">
            {/* File Upload Button with Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  disabled={disabled}
                  className={cn(
                    "shrink-0 rounded-full",
                    isMobile ? "h-8 w-8" : "h-9 w-9"
                  )}
                >
                  <Plus className={isMobile ? "h-4 w-4" : "h-5 w-5"} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-48">
                <DropdownMenuItem onClick={handleUploadFile}>
                  <Upload className="mr-2 h-4 w-4" />
                  <span>Upload file</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleCreateImage}>
                  <Image className="mr-2 h-4 w-4" />
                  <span>Upload image</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Tools Button with Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  disabled={disabled}
                  className={cn(
                    "shrink-0 rounded-full",
                    isMobile ? "h-8 w-8" : "h-9 w-9"
                  )}
                >
                  <Wrench className={isMobile ? "h-4 w-4" : "h-5 w-5"} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-48">
                <DropdownMenuItem onClick={handleCreateImage}>
                  <Image className="mr-2 h-4 w-4" />
                  <span>Create image</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleGenerateCode}>
                  <Code className="mr-2 h-4 w-4" />
                  <span>Generate code</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleAnalyzeDocument}>
                  <FileText className="mr-2 h-4 w-4" />
                  <span>Analyze document</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          
          {/* Send/Stop Button */}
          {isStreaming ? (
            <Button
              onClick={handleStop}
              size="icon"
              variant="secondary"
              className={cn(
                "shrink-0 rounded-full",
                isMobile ? "h-8 w-8" : "h-9 w-9"
              )}
            >
              <Square className={isMobile ? "h-4 w-4" : "h-5 w-5"} fill="currentColor" />
            </Button>
          ) : (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={handleSend}
                    disabled={disabled || !message.trim()}
                    size="icon"
                    className={cn(
                      "shrink-0 rounded-full",
                      isMobile ? "h-8 w-8" : "h-9 w-9"
                    )}
                  >
                    <Send className={isMobile ? "h-4 w-4" : "h-5 w-5"} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Send message</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </div>
      
      <p className={cn(
        "mt-2 text-muted-foreground",
        isMobile ? "text-[10px]" : "text-xs"
      )}>
        {isStreaming 
          ? "Press Enter to stop and send new message" 
          : "Press Enter to send, Shift+Enter for new line"
        }
      </p>
    </div>
  );
});
