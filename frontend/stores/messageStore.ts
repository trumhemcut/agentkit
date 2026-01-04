import { create } from 'zustand';
import { Message } from '@/types/chat';
import { messagesApi } from '@/services/api';
import { toast } from 'sonner';

interface MessageState {
  // State
  messagesByThread: Record<string, Message[]>;
  isLoadingMessages: Record<string, boolean>;
  
  // Actions
  loadMessages: (threadId: string) => Promise<void>;
  addMessage: (threadId: string, message: Message) => Promise<Message | null>;
  updateMessageContent: (threadId: string, messageId: string, content: string) => void;
  updateMessage: (threadId: string, messageId: string, updates: Partial<Message>) => void;
  getMessages: (threadId: string) => Message[];
  clearMessages: (threadId: string) => void;
}

export const useMessageStore = create<MessageState>((set, get) => ({
  // Initial state
  messagesByThread: {},
  isLoadingMessages: {},
  
  /**
   * Load messages for a thread from database
   */
  loadMessages: async (threadId: string) => {
    const { isLoadingMessages, messagesByThread } = get();
    
    // Skip if already loading or already loaded
    if (isLoadingMessages[threadId] || messagesByThread[threadId]) return;
    
    set(state => ({
      isLoadingMessages: { ...state.isLoadingMessages, [threadId]: true },
    }));
    
    try {
      const response = await messagesApi.list(threadId);
      const dbMessages = response.messages || [];
      
      // Convert database messages to chat messages
      const messages: Message[] = dbMessages.map(dbMsg => ({
        id: dbMsg.id,
        threadId: dbMsg.thread_id,
        role: dbMsg.role === 'user' ? 'user' : 'agent',
        content: dbMsg.content || '',
        timestamp: new Date(dbMsg.created_at).getTime(),
        agentId: dbMsg.agent_id, // Store agent_id to identify Canvas vs Chat mode
        messageType: dbMsg.message_type as 'text' | 'artifact', // Use message_type from database
        isInterrupted: dbMsg.is_interrupted, // Track if message was interrupted
        metadata: dbMsg.metadata || undefined,
        // Parse artifact_data if it's an artifact message
        ...(dbMsg.message_type === 'artifact' && dbMsg.artifact_data && {
          artifactType: dbMsg.artifact_data.type,
          language: dbMsg.artifact_data.language,
          title: dbMsg.artifact_data.title,
          artifactId: dbMsg.artifact_data.id,
        }),
      }));
      
      set(state => ({
        messagesByThread: {
          ...state.messagesByThread,
          [threadId]: messages,
        },
        isLoadingMessages: { ...state.isLoadingMessages, [threadId]: false },
      }));
      
      console.log('[MessageStore] Loaded messages for thread:', threadId, messages.length);
    } catch (error) {
      console.error('[MessageStore] Failed to load messages:', error);
      toast.error('Failed to load messages');
      set(state => ({
        isLoadingMessages: { ...state.isLoadingMessages, [threadId]: false },
      }));
    }
  },
  
  /**
   * Add message (optimistic update + database sync)
   */
  addMessage: async (threadId: string, message: Message, forceSave: boolean = false) => {
    // Check for duplicate before adding
    const existingMessages = get().messagesByThread[threadId] || [];
    const isDuplicate = existingMessages.some(m => m.id === message.id);
    
    if (isDuplicate && !forceSave) {
      console.log('[MessageStore] Skipping duplicate message:', message.id);
      return message;
    }
    
    // Optimistic update (only if not duplicate, or forceSave with update)
    if (!isDuplicate) {
      set(state => ({
        messagesByThread: {
          ...state.messagesByThread,
          [threadId]: [...existingMessages, message],
        },
      }));
    } else {
      // Update existing message
      set(state => ({
        messagesByThread: {
          ...state.messagesByThread,
          [threadId]: state.messagesByThread[threadId].map(m =>
            m.id === message.id ? { ...m, ...message } : m
          ),
        },
      }));
    }
    
    // Skip backend sync for pending/streaming messages (unless forceSave)
    if ((message.isPending || message.isStreaming) && !forceSave) {
      console.log('[MessageStore] Skipping backend sync for pending/streaming message');
      return message;
    }
    
    try {
      // Convert chat message to database format
      const createRequest: any = {
        role: message.role === 'user' ? 'user' : 'assistant',
        content: message.content || '',
        is_interrupted: message.isInterrupted || false,
      };
      
      // Add artifact data if it's an artifact message
      if (message.messageType === 'artifact') {
        createRequest.artifact_data = {
          type: message.artifactType,
          language: message.language,
          title: message.title,
          id: message.artifactId,
        };
      }
      
      // Add metadata if present
      if (message.metadata) {
        createRequest.metadata = message.metadata;
      }
      
      // Sync to database
      const savedMessage = await messagesApi.create(threadId, createRequest);
      
      // Update with backend ID and timestamp if different
      if (savedMessage.id !== message.id) {
        set(state => ({
          messagesByThread: {
            ...state.messagesByThread,
            [threadId]: state.messagesByThread[threadId].map(m =>
              m.id === message.id 
                ? {
                    ...m,
                    id: savedMessage.id,
                    timestamp: new Date(savedMessage.created_at).getTime(),
                  }
                : m
            ),
          },
        }));
      }
      
      console.log('[MessageStore] Added message to database:', savedMessage.id);
      return message;
    } catch (error) {
      console.error('[MessageStore] Failed to add message:', error);
      // Keep optimistic update but show error
      toast.error('Failed to save message');
      return message;
    }
  },
  
  /**
   * Update message content (for streaming updates)
   */
  updateMessageContent: (threadId: string, messageId: string, content: string) => {
    set(state => ({
      messagesByThread: {
        ...state.messagesByThread,
        [threadId]: state.messagesByThread[threadId]?.map(m =>
          m.id === messageId ? { ...m, content } : m
        ) || [],
      },
    }));
  },
  
  /**
   * Update message with partial updates (for streaming, artifacts, etc.)
   */
  updateMessage: (threadId: string, messageId: string, updates: Partial<Message>) => {
    set(state => ({
      messagesByThread: {
        ...state.messagesByThread,
        [threadId]: state.messagesByThread[threadId]?.map(m =>
          m.id === messageId ? { ...m, ...updates } : m
        ) || [],
      },
    }));
  },
  
  /**
   * Get messages for a thread
   */
  getMessages: (threadId: string) => {
    return get().messagesByThread[threadId] || [];
  },
  
  /**
   * Clear messages for a thread
   */
  clearMessages: (threadId: string) => {
    set(state => {
      const newMessagesByThread = { ...state.messagesByThread };
      delete newMessagesByThread[threadId];
      return { messagesByThread: newMessagesByThread };
    });
  },
}));
