# Database-First Migration Implementation Plan

**Requirement**: [031-database-first.md](../.docs/0-requirements/031-database-first.md)  
**Based on**: [030-database-persistence-layer-plan.md](030-database-persistence-layer-plan.md)  
**Created**: January 4, 2026  
**Status**: 🔄 Planning

## Overview

Migrate frontend from localStorage-first to database-first approach. The database persistence layer (plan 030) has been completed. Now we eliminate localStorage dependency and make the backend database the single source of truth. Use Zustand for frontend state management and caching when needed. Add Sonner toast for user notifications.

## Objectives

- ✅ Backend database layer is ready (from plan 030)
- 🎯 Remove localStorage as primary data source
- 🎯 Fetch threads and messages from database via API
- 🎯 Use Zustand for state management and optimistic UI updates
- 🎯 Add Sonner toast for notifications (success, errors, loading states)
- 🎯 Maintain existing camelCase/snake_case conventions (no conversion)
- 🎯 Keep optimistic UI updates for smooth UX
- 🎯 Handle offline scenarios gracefully

## Migration Strategy

### Phase 1: Backend Verification
Verify all necessary API endpoints are ready (already implemented in plan 030)

### Phase 2: Frontend State Management (Zustand)
Replace localStorage hooks with Zustand stores that sync with database

### Phase 3: Remove localStorage Dependencies
Clean up old localStorage code and storage service

### Phase 4: Error Handling & UX
Add toast notifications and proper error handling

---

## Backend Implementation

**Status**: ✅ Already Complete (from plan 030)

### Available API Endpoints

All endpoints are implemented in `backend/api/routes.py`:

1. **Thread Management**:
   - `POST /api/threads` - Create thread
   - `GET /api/threads` - List all threads
   - `GET /api/threads/{thread_id}` - Get thread by ID
   - `PUT /api/threads/{thread_id}` - Update thread (title)
   - `DELETE /api/threads/{thread_id}` - Delete thread

2. **Message Management**:
   - `POST /api/messages` - Create message
   - `GET /api/messages` - List messages by thread_id
   - `GET /api/messages/{message_id}` - Get message by ID
   - `DELETE /api/messages/{message_id}` - Delete message

### Data Models

**Backend**: Uses snake_case (SQLAlchemy models)
```python
# Thread model
{
  "id": "uuid",
  "title": "string",
  "agent_id": "string",
  "model": "string", 
  "provider": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}

# Message model
{
  "id": "uuid",
  "thread_id": "uuid",
  "role": "string",
  "content": "string",
  "artifact_data": "json_string",
  "message_metadata": "json_string",
  "created_at": "datetime"
}
```

**Frontend**: Uses unified types in `@/types` (single source of truth)
```typescript
interface Thread {
  id: string;
  title: string;
  agent_id: string;
  model: string;
  provider: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];  // Optional, loaded separately
}

interface Message {
  id: string;
  thread_id?: string;
  role: 'user' | 'assistant';
  content: string;
  artifact?: Artifact;  // Parsed object, not JSON string
  metadata?: Record<string, any>;  // Parsed object, not JSON string
  isPending?: boolean;
  isStreaming?: boolean;
  created_at?: string;
}
```

**Note**: All types are in `@/types` - no separate `@/types/database` or `@/types/chat`. The Message type supports both UI states (isPending, isStreaming) and database fields (thread_id, created_at).

---

## Frontend Implementation

**Delegate to Frontend Agent** - See [frontend.agent.md](../.github/agents/frontend.agent.md)

### 1. Install Dependencies

```bash
cd frontend
npm install sonner
# Zustand already installed (check package.json)
```

### 2. Setup Sonner Toast Provider

**File**: `frontend/app/layout.tsx`

Add Sonner Toaster component to root layout:

```typescript
import { Toaster } from 'sonner';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster 
          position="top-right"
          expand={false}
          richColors
          closeButton
        />
      </body>
    </html>
  );
}
```

### 3. Create Zustand Store for Threads

**File**: `frontend/stores/threadStore.ts` (NEW)

Create a Zustand store to manage threads with database sync:

```typescript
import { create } from 'zustand';
import { Thread } from '@/types';
import { threadsApi } from '@/services/api';
import { toast } from 'sonner';

interface ThreadState {
  // State
  threads: Thread[];
  currentThreadId: string | null;
  isLoading: boolean;
  isInitialized: boolean;
  
  // Actions
  loadThreads: () => Promise<void>;
  createThread: (agentId: string, model: string, provider: string) => Promise<Thread | null>;
  selectThread: (threadId: string) => void;
  updateThreadTitle: (threadId: string, title: string) => Promise<void>;
  deleteThread: (threadId: string) => Promise<void>;
  getThread: (threadId: string) => Thread | null;
}

export const useThreadStore = create<ThreadState>((set, get) => ({
  // Initial state
  threads: [],
  currentThreadId: null,
  isLoading: false,
  isInitialized: false,
  
  /**
   * Load all threads from database
   */
  loadThreads: async () => {
    const { isLoading, isInitialized } = get();
    
    // Prevent duplicate loads
    if (isLoading || isInitialized) return;
    
    set({ isLoading: true });
    
    try {
      const response = await threadsApi.list();
      const threads = response.threads || [];
      
      set({ 
        threads,
        isLoading: false,
        isInitialized: true,
        // Select first thread if none selected
        currentThreadId: threads.length > 0 ? threads[0].id : null
      });
      
      console.log('[ThreadStore] Loaded threads:', threads.length);
    } catch (error) {
      console.error('[ThreadStore] Failed to load threads:', error);
      toast.error('Failed to load threads');
      set({ isLoading: false, isInitialized: true });
    }
  },
  
  /**
   * Create new thread (database-first)
   */
  createThread: async (agentId: string, model: string, provider: string) => {
    try {
      // Show loading toast
      const toastId = toast.loading('Creating new chat...');
      
      // Create in database
      const newThread = await threadsApi.create({
        title: 'New Chat',
        agent_id: agentId,
        model,
        provider,
      });
      
      // Update store
      set(state => ({
        threads: [newThread, ...state.threads],
        currentThreadId: newThread.id,
      }));
      
      toast.success('New chat created', { id: toastId });
      console.log('[ThreadStore] Created thread:', newThread.id);
      
      return newThread;
    } catch (error) {
      console.error('[ThreadStore] Failed to create thread:', error);
      toast.error('Failed to create chat');
      return null;
    }
  },
  
  /**
   * Select thread
   */
  selectThread: (threadId: string) => {
    set({ currentThreadId: threadId });
  },
  
  /**
   * Update thread title (optimistic update)
   */
  updateThreadTitle: async (threadId: string, title: string) => {
    // Optimistic update
    set(state => ({
      threads: state.threads.map(t => 
        t.id === threadId 
          ? { ...t, title, updated_at: new Date().toISOString() }
          : t
      ),
    }));
    
    try {
      // Sync to database
      await threadsApi.update(threadId, { title });
      console.log('[ThreadStore] Updated thread title:', threadId);
    } catch (error) {
      console.error('[ThreadStore] Failed to update title:', error);
      toast.error('Failed to update title');
      // Revert on error
      get().loadThreads();
    }
  },
  
  /**
   * Delete thread (optimistic update)
   */
  deleteThread: async (threadId: string) => {
    // Optimistic update
    const prevThreads = get().threads;
    const prevCurrentId = get().currentThreadId;
    
    set(state => {
      const newThreads = state.threads.filter(t => t.id !== threadId);
      return {
        threads: newThreads,
        currentThreadId: state.currentThreadId === threadId 
          ? (newThreads[0]?.id || null)
          : state.currentThreadId,
      };
    });
    
    try {
      // Sync to database
      await threadsApi.delete(threadId);
      toast.success('Chat deleted');
      console.log('[ThreadStore] Deleted thread:', threadId);
    } catch (error) {
      console.error('[ThreadStore] Failed to delete thread:', error);
      toast.error('Failed to delete chat');
      // Revert on error
      set({ threads: prevThreads, currentThreadId: prevCurrentId });
    }
  },
  
  /**
   * Get thread by ID
   */
  getThread: (threadId: string) => {
    return get().threads.find(t => t.id === threadId) || null;
  },
}));
```

### 4. Create Zustand Store for Messages

**File**: `frontend/stores/messageStore.ts` (NEW)

Create a Zustand store to manage messages with database sync:

```typescript
import { create } from 'zustand';
import { Message } from '@/types';
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
      const messages = response.messages || [];
      
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
  addMessage: async (threadId: string, message: Message) => {
    // Optimistic update
    set(state => ({
      messagesByThread: {
        ...state.messagesByThread,
        [threadId]: [...(state.messagesByThread[threadId] || []), message],
      },
    }));
    
    // Skip backend sync for pending/streaming messages
    if (message.isPending || message.isStreaming) {
      console.log('[MessageStore] Skipping backend sync for pending/streaming message');
      return message;
    }
    
    try {
      // Sync to database
      const savedMessage = await messagesApi.create({
        thread_id: threadId,
        role: message.role,
        content: message.content || '',
        artifact_data: message.artifact ? JSON.stringify(message.artifact) : null,
        message_metadata: message.metadata ? JSON.stringify(message.metadata) : null,
      });
      
      // Update with backend ID if different
      if (savedMessage.id !== message.id) {
        set(state => ({
          messagesByThread: {
            ...state.messagesByThread,
            [threadId]: state.messagesByThread[threadId].map(m =>
              m.id === message.id ? savedMessage : m
            ),
          },
        }));
      }
      
      console.log('[MessageStore] Added message to database:', savedMessage.id);
      return savedMessage;
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
```

### 5. Update useChatThreads Hook

**File**: `frontend/hooks/useChatThreads.ts`

Replace localStorage logic with Zustand store:

```typescript
'use client';

import { useState, useEffect } from 'react';
import { Thread } from '@/types';
import { useThreadStore } from '@/stores/threadStore';

/**
 * Hook for managing chat threads (now database-first)
 * 
 * @param initialThreadId - Optional thread ID from URL params
 * @param agentId - Agent type for new threads (default: 'chat')
 * @param model - Model for new threads (default: 'qwen:7b')
 * @param provider - Provider for new threads (default: 'ollama')
 */
export function useChatThreads(
  initialThreadId?: string,
  agentId: string = 'chat',
  model: string = 'qwen:7b',
  provider: string = 'ollama'
) {
  const {
    threads,
    currentThreadId,
    isLoading,
    isInitialized,
    loadThreads,
    createThread: createThreadStore,
    selectThread,
    updateThreadTitle: updateTitleStore,
    deleteThread: deleteThreadStore,
  } = useThreadStore();
  
  // Load threads on mount
  useEffect(() => {
    if (!isInitialized) {
      loadThreads();
    }
  }, [isInitialized, loadThreads]);
  
  // Handle initial thread selection
  useEffect(() => {
    if (isInitialized && !currentThreadId && threads.length > 0) {
      if (initialThreadId && threads.some(t => t.id === initialThreadId)) {
        selectThread(initialThreadId);
      } else {
        selectThread(threads[0].id);
      }
    }
  }, [isInitialized, currentThreadId, initialThreadId, threads, selectThread]);
  
  // Auto-create first thread if no threads exist
  useEffect(() => {
    if (isInitialized && threads.length === 0) {
      createThreadStore(agentId, model, provider);
    }
  }, [isInitialized, threads.length, agentId, model, provider, createThreadStore]);
  
  return {
    threads,
    currentThreadId,
    isLoading,
    createThread: () => createThreadStore(agentId, model, provider),
    deleteThread: deleteThreadStore,
    selectThread,
    updateThreadTitle: updateTitleStore,
  };
}
```

### 6. Update useMessages Hook

**File**: `frontend/hooks/useMessages.ts`

Replace localStorage logic with Zustand store:

```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';
import { Message, isArtifactMessage } from '@/types/chat';
import { useMessageStore } from '@/stores/messageStore';
import { useAutoScroll } from './useAutoScroll';

export interface UseMessagesOptions {
  onArtifactDetected?: (message: Message) => void;
}

/**
 * Hook for managing messages in a thread (now database-first)
 */
export function useMessages(threadId: string | null, options?: UseMessagesOptions) {
  const {
    messagesByThread,
    isLoadingMessages,
    loadMessages,
    addMessage: addMessageStore,
    updateMessageContent: updateContentStore,
    getMessages,
  } = useMessageStore();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  
  // Use auto-scroll hook
  const { scrollRef, handleScroll, scrollToBottom, shouldAutoScroll } = useAutoScroll(
    [messages],
    { isInitialLoad }
  );
  
  // Load messages when thread changes
  useEffect(() => {
    if (!threadId) {
      setMessages([]);
      setIsInitialLoad(true);
      return;
    }
    
    setIsInitialLoad(true);
    setIsLoading(true);
    
    // Load from store
    loadMessages(threadId).then(() => {
      const messages = getMessages(threadId);
      setMessages(messages);
      setIsLoading(false);
      
      setTimeout(() => {
        setIsInitialLoad(false);
      }, 100);
    });
  }, [threadId, loadMessages, getMessages]);
  
  /**
   * Add a new message
   */
  const addMessage = useCallback((message: Message) => {
    // Update local state for immediate UI
    setMessages(prev => [...prev, message]);
    
    // Detect artifact messages
    if (isArtifactMessage(message) && options?.onArtifactDetected) {
      queueMicrotask(() => {
        options.onArtifactDetected?.(message);
      });
    }
    
    if (threadId) {
      // Sync to database
      addMessageStore(threadId, message);
    }
  }, [threadId, addMessageStore, options]);
  
  /**
   * Update message (for streaming)
   */
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, ...updates } : msg
    ));
    
    // Update store if content changed
    if (threadId && updates.content !== undefined) {
      updateContentStore(threadId, messageId, updates.content);
    }
  }, [threadId, updateContentStore]);
  
  return {
    messages,
    isLoading,
    addMessage,
    updateMessage,
    scrollRef,
    handleScroll,
    scrollToBottom,
    shouldAutoScroll,
  };
}
```

### 7. Remove/Deprecate StorageService

**File**: `frontend/services/storage.ts`

Two options:

**Option A**: Delete the file entirely (recommended)
- Remove all localStorage dependencies
- Update imports in other files

**Option B**: Add deprecation notice and keep minimal interface
```typescript
/**
 * @deprecated StorageService is deprecated. Use Zustand stores instead:
 * - useThreadStore for threads
 * - useMessageStore for messages
 */
export class StorageService {
  static getThreads() {
    console.warn('StorageService.getThreads is deprecated. Use useThreadStore.');
    return [];
  }
  // ... other deprecated methods
}
```

### 8. Update Chat Page Component

**File**: `frontend/app/chat/page.tsx`

Ensure the page uses the new hooks (likely already compatible, just verify):

```typescript
'use client';

import { useChatThreads } from '@/hooks/useChatThreads';
import { useMessages } from '@/hooks/useMessages';
// ... other imports

export default function ChatPage() {
  const { threads, currentThreadId, createThread, deleteThread, selectThread } = useChatThreads();
  const { messages, addMessage, updateMessage } = useMessages(currentThreadId);
  
  // Rest of component logic...
}
```

### 9. Update Model/Agent Selection Stores

**Files**: 
- `frontend/stores/modelStore.ts`
- `frontend/stores/agentStore.ts`

These stores already use Zustand with localStorage persistence. Keep them as-is for user preferences (model/agent selection doesn't need database persistence).

### 10. Testing Checklist

**Manual Testing**:
- [ ] Create new thread → verify saved to database
- [ ] Send message → verify saved to database
- [ ] Refresh page → threads and messages load from database
- [ ] Update thread title → verify saved to database
- [ ] Delete thread → verify deleted from database
- [ ] Test offline scenario → show appropriate errors with toast
- [ ] Test optimistic updates → UI updates immediately
- [ ] Test multiple browser tabs → changes sync properly

**Error Scenarios**:
- [ ] Network error → toast notification shown
- [ ] Database unavailable → graceful degradation
- [ ] Invalid data → validation errors shown

---

## Migration Checklist

### Preparation
- [ ] ✅ Verify database is running and migrated
- [ ] ✅ Verify all API endpoints are working
- [ ] Install sonner: `npm install sonner`
- [ ] Verify Zustand is installed

### Implementation Order
1. [ ] Add Sonner Toaster to layout
2. [ ] Create `threadStore.ts`
3. [ ] Create `messageStore.ts`
4. [ ] Update `useChatThreads.ts` hook
5. [ ] Update `useMessages.ts` hook
6. [ ] Remove/deprecate `StorageService`
7. [ ] Test thoroughly

### Cleanup
- [ ] Remove localStorage service code
- [ ] Remove unused imports
- [ ] Update documentation
- [ ] Update knowledge base in `.docs/2-knowledge-base/`

---

## Technical Considerations

### Optimistic Updates
- Update UI immediately for perceived performance
- Sync to database in background
- Revert on error with toast notification

### Error Handling
- Use Sonner toast for all user-facing errors
- Log detailed errors to console for debugging
- Provide clear error messages

### Data Consistency
- Database is single source of truth
- Zustand provides caching and state management
- No localStorage fallback (simplifies logic)

### Performance
- Load threads once on app init
- Load messages per thread on demand
- Use Zustand's shallow equality for efficient re-renders

### Naming Conventions
- **Keep existing conventions**: snake_case in backend, camelCase in frontend
- API client (`services/api.ts`) already handles conversion
- Don't change existing code unnecessarily

---

## Dependencies

### New Dependencies
- `sonner` - Toast notifications

### Existing Dependencies
- `zustand` - State management (already installed)
- Backend API endpoints (already implemented)

---

## Rollback Plan

If issues arise:
1. Keep localStorage code in a git branch before deletion
2. Can quickly revert hooks to use StorageService
3. Database data is preserved (won't be lost)
4. Zustand stores can coexist with old localStorage code

---

## Success Criteria

- ✅ No localStorage usage for threads/messages
- ✅ All thread/message operations sync to database
- ✅ Optimistic UI updates work smoothly
- ✅ Error handling with toast notifications
- ✅ Page refresh loads data from database
- ✅ Clean console logs (no localStorage warnings)
- ✅ Backward compatible with existing UI components

---

## Notes

- Keep model/agent selection in localStorage (user preferences, not critical data)
- Maintain existing camelCase/snake_case naming (no changes needed)
- Use toast.loading() for long operations
- Keep AG-UI protocol unchanged
- Update knowledge base after completion
