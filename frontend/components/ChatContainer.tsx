'use client';

import { useEffect, useState, useRef, forwardRef, useImperativeHandle } from 'react';
import { MessageHistory } from './MessageHistory';
import { ChatInput, ChatInputRef } from './ChatInput';
import { useMessages } from '@/hooks/useMessages';
import { useAGUI } from '@/hooks/useAGUI';
import { Message as ChatMessage } from '@/types/chat';
import { Message as APIMessage, sendChatMessage } from '@/services/api';
import { MessageSquare } from 'lucide-react';

interface ChatContainerProps {
  threadId: string | null;
  onUpdateThreadTitle: (threadId: string, title: string) => void;
}

export interface ChatContainerRef {
  focusInput: () => void;
}

/**
 * Chat Container component
 * 
 * Main chat interface with message history and input
 */
export const ChatContainer = forwardRef<ChatContainerRef, ChatContainerProps>(function ChatContainer({ threadId, onUpdateThreadTitle }, ref) {
  const { messages, addMessage, updateMessage, scrollRef } = useMessages(threadId);
  const { isConnected, on, getClient, setConnectionState } = useAGUI();
  const [isSending, setIsSending] = useState(false);
  const currentAgentMessageRef = useRef<ChatMessage | null>(null);
  const threadIdRef = useRef<string | null>(threadId);
  const chatInputRef = useRef<ChatInputRef>(null);

  useImperativeHandle(ref, () => ({
    focusInput: () => {
      chatInputRef.current?.focus();
    }
  }));

  // Keep threadId ref in sync
  useEffect(() => {
    threadIdRef.current = threadId;
  }, [threadId]);

  // Set connection state when thread is selected
  useEffect(() => {
    if (threadId) {
      // We're using on-demand streaming, so mark as connected when thread exists
      setConnectionState(true);
    } else {
      setConnectionState(false);
    }
  }, [threadId, setConnectionState]);

  // Handle AG-UI events - register once, not per thread
  useEffect(() => {
    // Handle RUN_STARTED
    const unsubscribeStart = on('RUN_STARTED', (event) => {
      console.log('Agent run started:', event);
    });

    // Handle TEXT_MESSAGE_START - new message begins
    const unsubscribeMessageStart = on('TEXT_MESSAGE_START', (event) => {
      console.log('Text message start:', event);
      const currentThreadId = threadIdRef.current;
      if (!currentThreadId) return;
      
      // If there's a pending message, update it to streaming
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg && currentMsg.isPending) {
        updateMessage(currentMsg.id, { isPending: false, isStreaming: true });
        currentAgentMessageRef.current = { ...currentMsg, isPending: false, isStreaming: true };
        return;
      }
      
      // Create new agent message
      const newMessage: ChatMessage = {
        id: event.message_id || `msg-agent-${Date.now()}`,
        threadId: currentThreadId,
        role: 'agent',
        content: '',
        timestamp: Date.now(),
        agentName: event.agentName || 'Agent',
        isStreaming: true,
        isPending: false,
      };
      currentAgentMessageRef.current = newMessage;
      addMessage(newMessage);
    });

    // Handle TEXT_MESSAGE_CONTENT - streaming chunks
    const unsubscribeContent = on('TEXT_MESSAGE_CONTENT', (event) => {
      const chunk = event.delta || '';
      console.log('Text message content:', chunk);
      
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg) {
        // Update existing message
        const updatedContent = currentMsg.content + chunk;
        const updatedMessage = { ...currentMsg, content: updatedContent };
        currentAgentMessageRef.current = updatedMessage;
        updateMessage(currentMsg.id, { content: updatedContent });
      }
    });

    // Handle TEXT_MESSAGE_END - message complete
    const unsubscribeMessageEnd = on('TEXT_MESSAGE_END', (event) => {
      console.log('Text message end:', event);
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg) {
        updateMessage(currentMsg.id, { isStreaming: false });
        currentAgentMessageRef.current = null;
      }
    });

    // Handle RUN_FINISHED
    const unsubscribeFinish = on('RUN_FINISHED', (event) => {
      console.log('Run finished:', event);
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg) {
        updateMessage(currentMsg.id, { isStreaming: false });
        currentAgentMessageRef.current = null;
      }
      setIsSending(false);
    });

    // Handle ERROR
    const unsubscribeError = on('ERROR', (event) => {
      console.error('AG-UI Error:', event);
      setIsSending(false);
      currentAgentMessageRef.current = null;
      setConnectionState(false, event.data?.message || event.message || 'Connection error');
    });

    // Handle RUN_ERROR
    const unsubscribeRunError = on('RUN_ERROR', (event) => {
      console.error('AG-UI Run Error:', event);
      setIsSending(false);
      currentAgentMessageRef.current = null;
      setConnectionState(false, event.message || 'Agent error');
    });

    return () => {
      console.log('Unsubscribing all event handlers');
      unsubscribeStart();
      unsubscribeMessageStart();
      unsubscribeContent();
      unsubscribeMessageEnd();
      unsubscribeFinish();
      unsubscribeError();
      unsubscribeRunError();
    };
  }, [on, addMessage, updateMessage, setConnectionState]); // Removed threadId!

  const handleSendMessage = async (content: string) => {
    if (!threadId || isSending) {
      console.log('Cannot send: threadId=', threadId, 'isSending=', isSending);
      return;
    }

    console.log('Sending message:', content);
    setIsSending(true);

    // Create user message
    const userMessage: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      threadId: threadId,
      role: 'user',
      content: content,
      timestamp: Date.now(),
    };

    // Add user message to chat
    addMessage(userMessage);

    // Add pending agent message immediately
    const pendingMessage: ChatMessage = {
      id: `msg-agent-pending-${Date.now()}`,
      threadId: threadId,
      role: 'agent',
      content: '',
      timestamp: Date.now(),
      agentName: 'Agent',
      isPending: true,
      isStreaming: false,
    };
    currentAgentMessageRef.current = pendingMessage;
    addMessage(pendingMessage);

    // Update thread title if it's the first message
    if (messages.length === 0) {
      const title = content.slice(0, 50) + (content.length > 50 ? '...' : '');
      onUpdateThreadTitle(threadId, title);
    }

    // Prepare messages for API
    const apiMessages: APIMessage[] = [
      ...messages.map(msg => ({
        role: msg.role === 'agent' ? 'assistant' : msg.role, // Convert 'agent' to 'assistant'
        content: msg.content,
      })),
      {
        role: 'user',
        content: content,
      },
    ];

    console.log('API messages:', apiMessages);

    // Generate unique run ID
    const runId = `run-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Send message to backend and process streaming response
    try {
      const client = getClient();
      
      await sendChatMessage(
        apiMessages,
        threadId,
        runId,
        (event) => {
          // Process each event through the AGUI client
          client.processEvent(event);
        }
      );
      
      // Stream completed - note: isSending will be reset by RUN_FINISHED event
      console.log('Message send stream completed');
    } catch (error) {
      console.error('Error sending message:', error);
      setIsSending(false);
      setConnectionState(false, error instanceof Error ? error.message : 'Unknown error');
    }
  };

  if (!threadId) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <MessageSquare className="mb-4 h-16 w-16 text-muted-foreground" />
          <h2 className="mb-2 text-2xl font-bold">Welcome to AgentKit</h2>
          <p className="text-muted-foreground mb-4">
            Select a chat or start a new conversation
          </p>
        </div>
        <ChatInput 
          ref={chatInputRef}
          onSendMessage={() => {}} 
          disabled={true}
          placeholder="Start a new chat to begin..."
        />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-hidden">
        <MessageHistory messages={messages} scrollRef={scrollRef} />
      </div>
      <ChatInput 
        ref={chatInputRef}
        onSendMessage={handleSendMessage} 
        disabled={isSending || !isConnected}
        placeholder={
          !isConnected 
            ? "Connecting to agent..." 
            : isSending 
            ? "Agent is responding..." 
            : "Type your message..."
        }
      />
    </div>
  );
});
