'use client';

import { useEffect, useState, useRef, forwardRef, useImperativeHandle } from 'react';
import { MessageHistory } from './MessageHistory';
import { ChatInput, ChatInputRef } from './ChatInput';
import { useMessages } from '@/hooks/useMessages';
import { useAGUI } from '@/hooks/useAGUI';
import { useModelSelection } from '@/hooks/useModelSelection';
import { useAgentSelection } from '@/hooks/useAgentSelection';
import { Message as ChatMessage } from '@/types/chat';
import { Message as APIMessage, sendChatMessage } from '@/services/api';
import { EventType } from '@/types/agui';
import { MessageSquare } from 'lucide-react';

interface ChatContainerProps {
  threadId: string | null;
  onUpdateThreadTitle: (threadId: string, title: string) => void;
  onRefreshThreads?: () => void;
  onArtifactDetected?: (message: ChatMessage) => void;
  onEnableCanvas?: (message: ChatMessage) => void;
}

export interface ChatContainerRef {
  focusInput: () => void;
}

/**
 * Chat Container component
 * 
 * Main chat interface with message history and input
 */
export const ChatContainer = forwardRef<ChatContainerRef, ChatContainerProps>(function ChatContainer({ threadId, onUpdateThreadTitle, onRefreshThreads, onArtifactDetected, onEnableCanvas }, ref) {
  const { messages, addMessage, updateMessage, removeMessage, scrollRef } = useMessages(threadId, {
    onArtifactDetected,
  });
  const { isConnected, on, getClient, setConnectionState } = useAGUI();
  const { selectedModel } = useModelSelection();
  const { selectedAgent } = useAgentSelection();
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
    console.log('[ChatContainer] Registering AG-UI event handlers');
    
    // Handle RUN_STARTED
    const unsubscribeStart = on(EventType.RUN_STARTED, (event) => {
      console.log('[ChatContainer] Agent run started:', event);
    });

    // Handle TEXT_MESSAGE_START - new message begins
    const unsubscribeMessageStart = on(EventType.TEXT_MESSAGE_START, (event) => {
      console.log('[ChatContainer] Text message start:', event);
      const currentThreadId = threadIdRef.current;
      if (!currentThreadId) return;
      
      const typedEvent = event as any;
      const isArtifact = typedEvent.metadata?.message_type === 'artifact';
      
      // If there's a pending message, update it to streaming
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg && currentMsg.isPending) {
        const updates: Partial<ChatMessage> = { 
          isPending: false, 
          isStreaming: true 
        };
        
        // If it's an artifact, add artifact metadata
        if (isArtifact) {
          updates.messageType = 'artifact';
          updates.artifactType = typedEvent.metadata.artifact_type;
          updates.language = typedEvent.metadata.language;
          updates.title = typedEvent.metadata.title;
        }
        
        updateMessage(currentMsg.id, updates);
        currentAgentMessageRef.current = { ...currentMsg, ...updates } as ChatMessage;
        return;
      }
      
      // Create new agent message
      const newMessage: ChatMessage = {
        id: typedEvent.message_id || `msg-agent-${Date.now()}`,
        threadId: currentThreadId,
        role: 'agent',
        content: '',
        timestamp: Date.now(),
        agentName: typedEvent.agentName || 'Agent',
        isStreaming: true,
        isPending: false,
        messageType: isArtifact ? 'artifact' : 'text',
        ...(isArtifact && {
          artifactType: typedEvent.metadata.artifact_type,
          language: typedEvent.metadata.language,
          title: typedEvent.metadata.title,
        }),
      };
      currentAgentMessageRef.current = newMessage;
      addMessage(newMessage);
    });

    // Handle TEXT_MESSAGE_CONTENT - streaming chunks
    const unsubscribeContent = on(EventType.TEXT_MESSAGE_CONTENT, (event) => {
      const chunk = (event as any).delta || '';
      console.log('[ChatContainer] Text message content chunk');
      
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
    const unsubscribeMessageEnd = on(EventType.TEXT_MESSAGE_END, (event) => {
      console.log('[ChatContainer] Text message end:', event);
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg) {
        updateMessage(currentMsg.id, { isStreaming: false });
        currentAgentMessageRef.current = null;
      }
      // Refresh threads to update sidebar with latest messages
      onRefreshThreads?.();
    });

    // Handle RUN_FINISHED
    const unsubscribeFinish = on(EventType.RUN_FINISHED, (event) => {
      console.log('[ChatContainer] Run finished:', event);
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg) {
        // If message has no content, remove it
        if (currentMsg.content.trim() === '') {
          console.log('[ChatContainer] Removing empty pending/streaming message');
          removeMessage(currentMsg.id);
        } else {
          // Message has content, mark as complete
          updateMessage(currentMsg.id, { isPending: false, isStreaming: false });
        }
        currentAgentMessageRef.current = null;
      }
      setIsSending(false);
      // Refresh threads to update sidebar with latest messages
      onRefreshThreads?.();
    });

    // Handle ERROR
    const unsubscribeError = on(EventType.ERROR, (event) => {
      console.error('[ChatContainer] AG-UI Error:', event);
      setIsSending(false);
      currentAgentMessageRef.current = null;
      const errorMsg = (event as any).data?.message || (event as any).message || 'Connection error';
      setConnectionState(false, errorMsg);
    });

    // Handle RUN_ERROR
    const unsubscribeRunError = on(EventType.RUN_ERROR, (event) => {
      console.error('[ChatContainer] AG-UI Run Error:', event);
      setIsSending(false);
      currentAgentMessageRef.current = null;
      const errorMsg = (event as any).message || 'Agent error';
      setConnectionState(false, errorMsg);
    });

    return () => {
      console.log('[ChatContainer] Unsubscribing all event handlers');
      unsubscribeStart();
      unsubscribeMessageStart();
      unsubscribeContent();
      unsubscribeMessageEnd();
      unsubscribeFinish();
      unsubscribeError();
      unsubscribeRunError();
    };
  }, [on, addMessage, updateMessage, removeMessage, setConnectionState, onRefreshThreads]);

  const handleSendMessage = async (content: string) => {
    if (!threadId || isSending) {
      console.log('Cannot send: threadId=', threadId, 'isSending=', isSending);
      return;
    }

    if (!selectedAgent) {
      console.error('Cannot send message: Agent not loaded yet');
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
    
    // Refresh threads to update sidebar immediately after adding user message
    onRefreshThreads?.();

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
        selectedModel || undefined,
        selectedAgent,
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
      <div className="flex-1 min-h-0 overflow-hidden">
        <MessageHistory messages={messages} scrollRef={scrollRef} onEnableCanvas={onEnableCanvas} />
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
