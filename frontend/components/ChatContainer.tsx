'use client';

import { useEffect, useState, useRef, forwardRef, useImperativeHandle, useCallback } from 'react';
import { MessageHistory } from './MessageHistory';
import { ChatInput, ChatInputRef } from './ChatInput';
import { useMessages } from '@/hooks/useMessages';
import { useAGUI } from '@/hooks/useAGUI';
import { useA2UIEvents } from '@/hooks/useA2UIEvents';
import { isA2UIMessage } from '@/types/a2ui';
import { useModelStore } from '@/stores/modelStore';
import { useAgentStore } from '@/stores/agentStore';
import { Message as ChatMessage } from '@/types/chat';
import { Message as APIMessage, sendChatMessage, sendCanvasMessage } from '@/services/api';
import { EventType, CanvasEventType } from '@/types/agui';
import { MessageSquare } from 'lucide-react';
import { useCanvasOptional } from '@/contexts/CanvasContext';

interface ChatContainerProps {
  threadId: string | null;
  onUpdateThreadTitle: (threadId: string, title: string) => void;
  onRefreshThreads?: () => void;
  onArtifactDetected?: (message: ChatMessage) => void;
  onEnableCanvas?: (message: ChatMessage) => void;
  canvasModeActive?: boolean;
}

export interface ChatContainerRef {
  focusInput: () => void;
}

/**
 * Chat Container component
 * 
 * Main chat interface with message history and input
 */
export const ChatContainer = forwardRef<ChatContainerRef, ChatContainerProps>(function ChatContainer({ threadId, onUpdateThreadTitle, onRefreshThreads, onArtifactDetected, onEnableCanvas, canvasModeActive = false }, ref) {
  const { messages, addMessage, updateMessage, removeMessage, scrollRef, handleScroll, scrollToBottom } = useMessages(threadId, {
    onArtifactDetected,
  });
  const { isConnected, on, getClient, setConnectionState } = useAGUI();
  const { processA2UIMessage } = useA2UIEvents();
  // Only subscribe to selectedProvider - won't re-render on other model store changes
  const selectedProvider = useModelStore((state) => state.selectedProvider);
  // Only subscribe to selectedModel - won't re-render on other model store changes
  const selectedModel = useModelStore((state) => state.selectedModel);
  // Only subscribe to selectedAgent - won't re-render on other agent store changes
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  
  // Debug log to track selectedModel changes
  useEffect(() => {
    console.log('[ChatContainer] selectedProvider changed to:', selectedProvider);
    console.log('[ChatContainer] selectedModel changed to:', selectedModel);
  }, [selectedProvider, selectedModel]);
  const [isSending, setIsSending] = useState(false);
  const currentAgentMessageRef = useRef<ChatMessage | null>(null);
  const threadIdRef = useRef<string | null>(threadId);
  const chatInputRef = useRef<ChatInputRef>(null);
  
  // Get canvas context if available
  const canvasContext = useCanvasOptional();
  
  // Register chat input ref with canvas context if available
  useEffect(() => {
    if (canvasContext?.setChatInputRef) {
      canvasContext.setChatInputRef(chatInputRef);
    }
  }, [canvasContext]);

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
    
    // Handle all events to check for A2UI messages
    const unsubscribeAll = on('*', (event) => {
      // Check if this is an A2UI message and process it
      if (isA2UIMessage(event)) {
        console.log('[ChatContainer] A2UI message detected:', event);
        // Associate A2UI surface with current agent message
        const messageId = currentAgentMessageRef.current?.id;
        processA2UIMessage(event, messageId);
      }
    });
    
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
        
        // Extract agentId from metadata if available
        if (typedEvent.metadata?.agentId) {
          updates.agentId = typedEvent.metadata.agentId;
        }
        if (typedEvent.metadata?.agentName) {
          updates.agentName = typedEvent.metadata.agentName;
        }
        
        // If it's an artifact, add artifact metadata
        if (isArtifact) {
          updates.messageType = 'artifact';
          updates.artifactType = typedEvent.metadata.artifact_type;
          updates.language = typedEvent.metadata.language;
          updates.title = typedEvent.metadata.title;
          updates.artifactId = typedEvent.metadata.artifact_id;
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
        agentName: typedEvent.metadata?.agentName || typedEvent.agentName || 'Agent',
        agentId: typedEvent.metadata?.agentId,  // Extract agentId from metadata
        isStreaming: true,
        isPending: false,
        messageType: isArtifact ? 'artifact' : 'text',
        ...(isArtifact && {
          artifactType: typedEvent.metadata.artifact_type,
          language: typedEvent.metadata.language,
          title: typedEvent.metadata.title,
          artifactId: typedEvent.metadata.artifact_id,
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
        
        // If this is an artifact message, sync to canvas context
        if (currentMsg.messageType === 'artifact' && canvasContext) {
          const artifact = {
            artifact_id: currentMsg.artifactId || currentMsg.id,
            title: currentMsg.title || 'Artifact',
            content: currentMsg.content,
            language: currentMsg.language || 'text',
          };
          canvasContext.setArtifact(artifact);
          console.log('[ChatContainer] Synced artifact to canvas context:', artifact.artifact_id);
        }
        
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
      console.error('[ChatContainer] AG-UI Error:', JSON.stringify(event, null, 2));
      setIsSending(false);
      currentAgentMessageRef.current = null;
      
      // Try to extract error message from various possible locations
      const typedEvent = event as any;
      const errorMsg = typedEvent.message || 
                      typedEvent.error?.message || 
                      typedEvent.data?.message || 
                      'Connection error';
      
      console.error('[ChatContainer] Error message:', errorMsg);
      setConnectionState(false, errorMsg);
    });

    // Handle RUN_ERROR
    const unsubscribeRunError = on(EventType.RUN_ERROR, (event) => {
      // Check if event is actually empty
      const eventKeys = Object.keys(event || {});
      console.error('[ChatContainer] AG-UI Run Error - Keys:', eventKeys);
      console.error('[ChatContainer] AG-UI Run Error - Full event:', JSON.stringify(event, null, 2));
      
      setIsSending(false);
      currentAgentMessageRef.current = null;
      
      // Try to extract error message from various possible locations
      const typedEvent = event as any;
      const errorMsg = typedEvent.message || 
                      typedEvent.error?.message || 
                      typedEvent.data?.message || 
                      'Agent error occurred';
      
      console.error('[ChatContainer] Error message extracted:', errorMsg);
      setConnectionState(false, errorMsg);
    });

    // Handle CUSTOM events for canvas partial updates
    const unsubscribeCustom = on(EventType.CUSTOM, (event) => {
      const customEvent = event as any;
      console.log('[ChatContainer] CUSTOM event:', customEvent.name);
      
      if (!canvasContext) return;
      
      switch (customEvent.name) {
        case 'artifact_partial_update_start':
          console.log('[ChatContainer] Partial update START event:', {
            selection: customEvent.value.selection,
            hasStart: customEvent.value.selection && 'start' in customEvent.value.selection,
            hasEnd: customEvent.value.selection && 'end' in customEvent.value.selection,
            startValue: customEvent.value.selection?.start,
            endValue: customEvent.value.selection?.end
          });
          if (customEvent.value?.selection) {
            canvasContext.startPartialUpdate(customEvent.value.selection);
          }
          break;
          
        case 'artifact_partial_update_chunk':
          console.log('[ChatContainer] Partial update chunk:', customEvent.value?.chunk);
          if (customEvent.value?.chunk) {
            canvasContext.appendPartialUpdateChunk(customEvent.value.chunk);
          }
          break;
          
        case 'artifact_partial_update_complete':
          console.log('[ChatContainer] Partial update complete:', customEvent.value);
          canvasContext.completePartialUpdate();
          break;
      }
    });

    return () => {
      console.log('[ChatContainer] Unsubscribing all event handlers');
      unsubscribeAll();
      unsubscribeStart();
      unsubscribeMessageStart();
      unsubscribeContent();
      unsubscribeMessageEnd();
      unsubscribeFinish();
      unsubscribeError();
      unsubscribeRunError();
      unsubscribeCustom();
    };
  }, [on, addMessage, updateMessage, removeMessage, setConnectionState, onRefreshThreads, canvasContext, processA2UIMessage]);
  
  /**
   * Handle events from A2UI user actions
   * Process them through the same AGUI client as chat messages
   */
  const handleA2UIActionEvent = useCallback((event: any) => {
    console.log('[ChatContainer] Processing A2UI action event:', event.type);
    const client = getClient();
    client.processEvent(event);
  }, [getClient]);

  const handleSendMessage = async (content: string) => {
    if (!threadId || isSending) {
      console.log('Cannot send: threadId=', threadId, 'isSending=', isSending);
      return;
    }

    if (!selectedAgent) {
      console.error('Cannot send message: Agent not loaded yet');
      return;
    }

    console.log('[ChatContainer] Sending message:', content);
    console.log('[ChatContainer] Selected model:', selectedModel);
    console.log('[ChatContainer] Model from localStorage:', localStorage.getItem('selected-llm-model'));
    console.log('[ChatContainer] Will send model to API:', selectedModel || undefined);
    setIsSending(true);

    // Get selected text from canvas context if available
    const selectedTextForChat = canvasContext?.selectedTextForChat;

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
    
    // Force scroll to bottom when user sends a message
    setTimeout(() => scrollToBottom(true), 0);

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

    // Prepare selected text if available from canvas context
    // Use the full SelectedText object which includes actual start/end positions
    const selectedTextData = selectedTextForChat;

    if (selectedTextData) {
      console.log('[ChatContainer] Selected text from canvas:', {
        start: selectedTextData.start,
        end: selectedTextData.end,
        textLength: selectedTextData.text.length,
        textPreview: selectedTextData.text.substring(0, 50) + '...'
      });
    }

    // Generate unique run ID
    const runId = `run-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Send message to backend and process streaming response
    try {
      const client = getClient();
      
      // Use canvas message API if there's selected text from canvas
      if (selectedTextData) {
        // Get artifactId from canvas context
        const artifactIdToSend = canvasContext?.artifactId;
        
        console.log('[ChatContainer] Sending canvas message with artifactId:', artifactIdToSend);
        
        await sendCanvasMessage(
          apiMessages,
          threadId,
          runId,
          canvasContext?.artifact,
          artifactIdToSend || undefined,
          selectedTextData,
          undefined, // action - let backend determine
          selectedModel || undefined,
          selectedProvider || undefined,
          selectedAgent,
          (event) => {
            client.processEvent(event);
          }
        );
        
        // Clear selected text after sending
        canvasContext?.setSelectedTextForChat?.(null);
      } else {
        await sendChatMessage(
          apiMessages,
          threadId,
          runId,
          selectedModel || undefined,
          selectedProvider || undefined,
          selectedAgent,
          (event) => {
            // Process each event through the AGUI client
            client.processEvent(event);
          }
        );
      }
      
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

  // Check if we have messages to determine layout
  const hasMessages = messages.length > 0;

  return (
    <div className={canvasModeActive ? "flex h-full flex-col chat-container-canvas-border" : "flex h-full flex-col"}>
      {hasMessages ? (
        // Normal chat layout with messages
        <>
          <div className="flex-1 min-h-0">
            <MessageHistory 
              messages={messages} 
              scrollRef={scrollRef} 
              onEnableCanvas={onEnableCanvas}
              onScroll={handleScroll}
              canvasModeActive={canvasModeActive}
              threadId={threadId}
              onActionEvent={handleA2UIActionEvent}
            />
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
                : canvasContext?.selectedTextForChat
                ? "Ask about the selected text..."
                : "Type your message..."
            }
          />
        </>
      ) : (
        // Centered empty state layout
        <div className="flex h-full flex-col items-center justify-center pb-32">
          <div className="flex flex-col items-center justify-center max-w-4xl w-full px-4">
            <h3 className="mb-3 text-2xl font-semibold">Start a conversation</h3>
            <p className="text-sm text-muted-foreground mb-6 text-center">
              Ask me anything or start with a simple question
            </p>
            <div className="w-full">
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
          </div>
        </div>
      )}
    </div>
  );
});
