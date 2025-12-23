'use client';

import { useEffect, useState, useRef } from 'react';
import { MessageHistory } from '@/components/MessageHistory';
import { ChatInput } from '@/components/ChatInput';
import { useMessages } from '@/hooks/useMessages';
import { useAGUI } from '@/hooks/useAGUI';
import { useCanvas } from '@/contexts/CanvasContext';
import { useModelSelection } from '@/hooks/useModelSelection';
import { Message as ChatMessage } from '@/types/chat';
import { Message as APIMessage, sendCanvasMessage } from '@/services/api';
import { EventType } from '@/types/agui';
import { ArtifactV3 } from '@/types/canvas';
import { FileText } from 'lucide-react';

interface CanvasChatContainerProps {
  threadId: string;
}

/**
 * Canvas Chat Container component
 * 
 * Chat interface specifically for canvas mode with artifact integration
 */
export function CanvasChatContainer({ threadId }: CanvasChatContainerProps) {
  const { messages, addMessage, updateMessage, scrollRef } = useMessages(threadId);
  const { isConnected, on, getClient, setConnectionState } = useAGUI();
  const { selectedModel } = useModelSelection();
  const { 
    artifact, 
    setArtifact, 
    setIsArtifactStreaming, 
    appendStreamingContent, 
    clearStreamingContent 
  } = useCanvas();
  const [isSending, setIsSending] = useState(false);
  const currentAgentMessageRef = useRef<ChatMessage | null>(null);
  const threadIdRef = useRef<string | null>(threadId);

  // Keep threadId ref in sync
  useEffect(() => {
    threadIdRef.current = threadId;
  }, [threadId]);

  // Set connection state when thread is selected
  useEffect(() => {
    if (threadId) {
      setConnectionState(true);
    } else {
      setConnectionState(false);
    }
  }, [threadId, setConnectionState]);

  // Handle AG-UI events
  useEffect(() => {
    console.log('[CanvasChatContainer] Registering AG-UI event handlers');
    
    // Handle RUN_STARTED
    const unsubscribeStart = on(EventType.RUN_STARTED, (event) => {
      console.log('[CanvasChatContainer] Agent run started:', event);
    });

    // Handle TEXT_MESSAGE_START - new message begins
    const unsubscribeMessageStart = on(EventType.TEXT_MESSAGE_START, (event) => {
      console.log('[CanvasChatContainer] Text message start:', event);
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
        id: (event as any).message_id || `msg-agent-${Date.now()}`,
        threadId: currentThreadId,
        role: 'agent',
        content: '',
        timestamp: Date.now(),
        agentName: (event as any).agentName || 'Canvas Agent',
        isStreaming: true,
        isPending: false,
      };
      currentAgentMessageRef.current = newMessage;
      addMessage(newMessage);
    });

    // Handle TEXT_MESSAGE_CONTENT - streaming chunks
    const unsubscribeContent = on(EventType.TEXT_MESSAGE_CONTENT, (event) => {
      const chunk = (event as any).delta || '';
      console.log('[CanvasChatContainer] Text message content chunk');
      
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg) {
        const updatedContent = currentMsg.content + chunk;
        updateMessage(currentMsg.id, { content: updatedContent });
        currentAgentMessageRef.current = { ...currentMsg, content: updatedContent };
      }
    });

    // Handle TEXT_MESSAGE_END - message complete
    const unsubscribeMessageEnd = on(EventType.TEXT_MESSAGE_END, (event) => {
      console.log('[CanvasChatContainer] Text message end:', event);
      const currentMsg = currentAgentMessageRef.current;
      if (currentMsg) {
        updateMessage(currentMsg.id, { isStreaming: false });
        currentAgentMessageRef.current = null;
      }
    });

    // Handle RUN_FINISHED
    const unsubscribeFinish = on(EventType.RUN_FINISHED, (event) => {
      console.log('[CanvasChatContainer] Agent run finished:', event);
      setIsSending(false);
    });
    
    // Handle canvas-specific artifact events (direct events, not CUSTOM)
    const unsubscribeArtifactCreated = on('artifact_created', (event) => {
      console.log('[CanvasChatContainer] Artifact created event:', event);
      setIsSending(false);
    });
    
    const unsubscribeArtifactUpdated = on('artifact_updated', (event) => {
      console.log('[CanvasChatContainer] Artifact updated event:', event);
      setIsSending(false);
    });

    // Handle ERROR events
    const unsubscribeError = on(EventType.ERROR, (event) => {
      console.error('[CanvasChatContainer] AG-UI Error:', event);
      const errorMsg = (event as any).message || (event as any).error || JSON.stringify(event) || 'Unknown error';
      setIsSending(false);
      setConnectionState(false, errorMsg);
    });

    // Handle RUN_ERROR events
    const unsubscribeRunError = on(EventType.RUN_ERROR, (event) => {
      console.error('[CanvasChatContainer] Run Error:', event);
      const errorMsg = (event as any).message || (event as any).error || JSON.stringify(event) || 'Run error occurred';
      setIsSending(false);
      setConnectionState(false, errorMsg);
    });

    // Handle CUSTOM canvas events
    const unsubscribeCustom = on(EventType.CUSTOM, (event) => {
      const customEvent = event as any;
      const eventName = customEvent.name;
      const eventValue = customEvent.value;
      
      console.log('[CanvasChatContainer] Custom event:', eventName, eventValue);
      
      switch (eventName) {
        case 'thinking':
          console.log('[Canvas] Agent thinking:', eventValue.message);
          break;
          
        case 'artifact_streaming_start':
          console.log('[Canvas] Artifact streaming start:', eventValue);
          setIsArtifactStreaming(true);
          clearStreamingContent();
          break;
          
        case 'artifact_streaming':
          console.log('[Canvas] Artifact streaming chunk');
          appendStreamingContent(eventValue.contentDelta || '');
          break;
          
        case 'artifact_created':
          console.log('[Canvas] Artifact created:', eventValue.artifact);
          setArtifact(eventValue.artifact as ArtifactV3);
          setIsArtifactStreaming(false);
          clearStreamingContent();
          // Clear sending state when artifact is complete
          setIsSending(false);
          break;
          
        case 'artifact_updated':
          console.log('[Canvas] Artifact updated:', eventValue.artifact);
          setArtifact(eventValue.artifact as ArtifactV3);
          setIsArtifactStreaming(false);
          clearStreamingContent();
          // Clear sending state when artifact is complete
          setIsSending(false);
          break;
          
        default:
          console.log('[Canvas] Unknown custom event:', eventName);
      }
    });

    return () => {
      console.log('[CanvasChatContainer] Unsubscribing all event handlers');
      unsubscribeStart();
      unsubscribeMessageStart();
      unsubscribeContent();
      unsubscribeMessageEnd();
      unsubscribeFinish();
      unsubscribeArtifactCreated();
      unsubscribeArtifactUpdated();
      unsubscribeError();
      unsubscribeRunError();
      unsubscribeCustom();
    };
  }, [on, addMessage, updateMessage, setConnectionState, setArtifact, setIsArtifactStreaming, appendStreamingContent, clearStreamingContent]);

  const handleSendMessage = async (content: string) => {
    if (!threadId || isSending) {
      console.log('Cannot send: threadId=', threadId, 'isSending=', isSending);
      return;
    }

    console.log('Sending canvas message:', content);
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
      agentName: 'Canvas Agent',
      isPending: true,
      isStreaming: false,
    };
    currentAgentMessageRef.current = pendingMessage;
    addMessage(pendingMessage);

    // Prepare messages for API
    const apiMessages: APIMessage[] = [
      ...messages.map(msg => ({
        role: msg.role === 'agent' ? 'assistant' : msg.role,
        content: msg.content,
      })),
      {
        role: 'user',
        content: content,
      },
    ];

    console.log('Canvas API messages:', apiMessages, 'Artifact:', artifact);

    // Generate unique run ID
    const runId = `run-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Send canvas message to backend and process streaming response
    try {
      const client = getClient();
      
      await sendCanvasMessage(
        apiMessages,
        threadId,
        runId,
        artifact || undefined,
        undefined, // selectedText - can be added later
        undefined, // action - let backend determine
        selectedModel || undefined,
        (event) => {
          // Process each event through the AGUI client
          client.processEvent(event);
        }
      );
      
      console.log('Canvas message send stream completed');
    } catch (error) {
      console.error('Error sending canvas message:', error);
      setIsSending(false);
      setConnectionState(false, error instanceof Error ? error.message : 'Unknown error');
    }
  };

  return (
    <div className="flex h-full flex-col">
      {messages.length === 0 && !artifact && (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
          <FileText className="mb-4 h-16 w-16 text-muted-foreground" />
          <h2 className="mb-2 text-2xl font-bold">Canvas Mode</h2>
          <p className="text-muted-foreground mb-4 max-w-md">
            Chat with AI to create and edit code or text artifacts.
            <br />
            Your creations will appear on the right side.
          </p>
        </div>
      )}
      
      <div className="flex-1 overflow-hidden">
        <MessageHistory messages={messages} scrollRef={scrollRef} />
      </div>
      
      <ChatInput 
        onSendMessage={handleSendMessage} 
        disabled={isSending || !isConnected}
        placeholder={
          !isConnected 
            ? "Connecting to canvas agent..." 
            : isSending 
            ? "Agent is working..." 
            : "Ask me to create or edit something..."
        }
      />
    </div>
  );
}
