# Implementation Plan: Frontend Skeleton for Agentic AI Solution

**Requirement Reference**: [002-frontend-skeleton.md](../.docs/0-requirements/002-frontend-skeleton.md)

**Date**: December 23, 2025

## Overview

Build a NextJS frontend application with Shadcn UI and AG-UI protocol for agent-frontend communication. The application will feature a chat interface with thread management and real-time agent communication.

## Technology Stack

- **Framework**: NextJS (App Router)
- **UI Library**: Shadcn UI (built on Radix UI + Tailwind CSS)
- **Agent Protocol**: AG-UI (`@ag-ui/client`)
- **Icons**: Lucide React
- **Persistence**: LocalStorage for chat threads
- **Language**: TypeScript

## Architecture Components

### 1. Layout Structure
```
┌─────────────────────────────────────┐
│           Header                     │
├──────────┬──────────────────────────┤
│          │                           │
│  Left    │   Main Content            │
│  Sidebar │   - Chat History          │
│          │   - Chat Input Box        │
│          │                           │
└──────────┴──────────────────────────┘
```

### 2. Key Features
- **Header**: Application title and navigation
- **Left Sidebar**: New chat button, chat thread list
- **Main Content**: Chat history display, message input box
- **Avatar Icons**: Beautiful SVG icons for agents and humans (Lucide React)
- **Real-time Updates**: AG-UI event stream processing
- **Persistence**: LocalStorage for thread data

## Implementation Steps

### Phase 1: Project Setup

#### 1.1 Initialize NextJS Project
- [ ] Create NextJS app with TypeScript and App Router
- [ ] Configure Tailwind CSS
- [ ] Set up project structure (`/frontend` directory)

#### 1.2 Install Dependencies
```bash
npm install @ag-ui/client lucide-react
npx shadcn-ui@latest init
```

#### 1.3 Install Shadcn UI Components
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add card
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add separator
```

### Phase 2: Core Infrastructure

#### 2.1 Type Definitions (`/src/types/`)
- [ ] Create `chat.ts` - Chat message, thread, and conversation types
- [ ] Create `agent.ts` - Agent state and event types
- [ ] Create `agui.ts` - AG-UI protocol event types

**Example Types:**
```typescript
// types/chat.ts
export interface Message {
  id: string;
  threadId: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  agentName?: string;
}

export interface Thread {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

// types/agui.ts
export type AGUIEventType = 
  | 'RUN_STARTED'
  | 'TEXT_MESSAGE_CHUNK'
  | 'RUN_FINISHED'
  | 'THINKING'
  | 'ERROR';

export interface AGUIEvent {
  type: AGUIEventType;
  data: any;
  timestamp: number;
}
```

#### 2.2 Services Layer (`/src/services/`)

**2.2.1 LocalStorage Service** (`storage.ts`)
- [ ] Implement thread CRUD operations
- [ ] Implement message persistence
- [ ] Handle data serialization/deserialization
- [ ] Export helper functions: `getThreads()`, `saveThread()`, `deleteThread()`

**2.2.2 AG-UI Client Service** (`agui-client.ts`)
- [ ] Initialize AG-UI client
- [ ] Implement event stream connection
- [ ] Handle SSE events (RUN_STARTED, TEXT_MESSAGE_CHUNK, RUN_FINISHED, etc.)
- [ ] Implement reconnection logic
- [ ] Export `connectToAgent()`, `sendMessage()`, `disconnect()`

**2.2.3 API Client** (`api.ts`)
- [ ] Create typed API client for backend endpoints
- [ ] Implement request/response interceptors
- [ ] Handle error states
- [ ] Export functions: `sendChatMessage()`, `getAgentStatus()`

### Phase 3: React Hooks (`/src/hooks/`)

#### 3.1 Chat Management Hook
- [ ] Create `useChatThreads.ts`
  - Manage thread state
  - LocalStorage integration
  - Thread CRUD operations
  - Export: `createThread()`, `deleteThread()`, `selectThread()`

#### 3.2 AG-UI Integration Hook
- [ ] Create `useAGUI.ts`
  - Connect to AG-UI event stream
  - Process incoming events
  - Update chat state in real-time
  - Export: `messages`, `isConnected`, `sendMessage()`

#### 3.3 Message State Hook
- [ ] Create `useMessages.ts`
  - Manage message list per thread
  - Handle message updates
  - Auto-scroll to latest message
  - Export: `messages`, `addMessage()`, `updateMessage()`

### Phase 4: UI Components (`/src/components/`)

#### 4.1 Layout Components

**4.1.1 Header Component** (`Header.tsx`)
- [ ] Application title/logo
- [ ] Navigation elements
- [ ] Use Shadcn UI components

**4.1.2 Sidebar Component** (`Sidebar.tsx`)
- [ ] "New Chat" button (Shadcn Button)
- [ ] Thread list (Shadcn ScrollArea)
- [ ] Thread selection handler
- [ ] Thread delete button
- [ ] Empty state UI

**4.1.3 Main Layout** (`Layout.tsx`)
- [ ] Compose Header, Sidebar, and Main content
- [ ] Responsive grid layout
- [ ] Handle mobile breakpoints

#### 4.2 Chat Components

**4.2.1 Chat Container** (`ChatContainer.tsx`)
- [ ] Wrap ChatHistory and ChatInput
- [ ] Handle thread selection
- [ ] Connect to AG-UI hook
- [ ] Empty state when no thread selected

**4.2.2 Chat History** (`ChatHistory.tsx`)
- [ ] Display message list (Shadcn ScrollArea)
- [ ] Render MessageBubble components
- [ ] Auto-scroll to bottom on new messages
- [ ] Loading states

**4.2.3 Message Bubble** (`MessageBubble.tsx`)
- [ ] Display user/agent avatar (Lucide icons)
- [ ] Message content (Shadcn Card)
- [ ] Timestamp
- [ ] Agent name for agent messages
- [ ] Conditional styling based on role

**4.2.4 Chat Input** (`ChatInput.tsx`)
- [ ] Message input field (Shadcn Textarea)
- [ ] Send button (Shadcn Button)
- [ ] Handle Enter key submission
- [ ] Disable during agent response
- [ ] Character count (optional)

#### 4.3 Icon Components

**4.3.1 Avatar Icons** (`AvatarIcon.tsx`)
- [ ] User icon (Lucide `User` icon)
- [ ] Agent icon (Lucide `Bot` or `Cpu` icon)
- [ ] Wrapped in Shadcn Avatar component
- [ ] Customizable colors

### Phase 5: Pages (`/src/app/`)

#### 5.1 Home Page (`page.tsx`)
- [ ] Compose Layout with ChatContainer
- [ ] Initialize AG-UI connection
- [ ] Handle thread state
- [ ] Error boundaries

#### 5.2 Global Styles (`globals.css`)
- [ ] Import Tailwind CSS
- [ ] Define CSS variables for Shadcn UI theme
- [ ] Custom scrollbar styles (optional)

#### 5.3 Root Layout (`layout.tsx`)
- [ ] Set up HTML metadata
- [ ] Import global styles
- [ ] Configure fonts (optional)

### Phase 6: AG-UI Integration Details

#### 6.1 Event Stream Connection
```typescript
// Pseudo-code for AG-UI integration
import { AGUIClient } from '@ag-ui/client';

const client = new AGUIClient({
  endpoint: '/api/agent/stream'
});

client.on('RUN_STARTED', (event) => {
  // Show "Agent is thinking..." indicator
});

client.on('TEXT_MESSAGE_CHUNK', (event) => {
  // Append chunk to current message
});

client.on('RUN_FINISHED', (event) => {
  // Finalize message, save to localStorage
});
```

#### 6.2 Backend API Endpoints
**Expected endpoints** (to be implemented by Backend Agent):
- `POST /api/chat/message` - Send user message
- `GET /api/agent/stream` - SSE endpoint for AG-UI events

### Phase 7: Testing & Polish

#### 7.1 Functionality Testing
- [ ] Test thread creation and deletion
- [ ] Test message sending and receiving
- [ ] Test AG-UI event stream processing
- [ ] Test LocalStorage persistence
- [ ] Test responsive layout

#### 7.2 UI/UX Polish
- [ ] Add loading spinners
- [ ] Add error messages
- [ ] Add empty states
- [ ] Smooth animations (Tailwind transitions)
- [ ] Accessibility checks (ARIA labels, keyboard navigation)

#### 7.3 Documentation
- [ ] Update knowledge base in `/.docs/2-knowledge-base/frontend/`
- [ ] Document component API
- [ ] Document AG-UI integration patterns
- [ ] Add usage examples

## Folder Structure

```
/frontend
  /src
    /app
      layout.tsx          # Root layout
      page.tsx            # Home page
      globals.css         # Global styles
    /components
      Header.tsx          # Header component
      Sidebar.tsx         # Sidebar with threads
      ChatContainer.tsx   # Main chat container
      ChatHistory.tsx     # Message history
      MessageBubble.tsx   # Individual message
      ChatInput.tsx       # Input box
      AvatarIcon.tsx      # User/Agent icons
    /hooks
      useChatThreads.ts   # Thread management
      useAGUI.ts          # AG-UI integration
      useMessages.ts      # Message state
    /services
      storage.ts          # LocalStorage service
      agui-client.ts      # AG-UI client wrapper
      api.ts              # Backend API client
    /types
      chat.ts             # Chat types
      agent.ts            # Agent types
      agui.ts             # AG-UI event types
  /public
    # Static assets
  package.json
  tsconfig.json
  tailwind.config.ts
  next.config.js
```

## Dependencies

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@ag-ui/client": "latest",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.0.0",
    "autoprefixer": "^10.0.0",
    "postcss": "^8.0.0"
  }
}
```

## Success Criteria

✅ NextJS app running with TypeScript
✅ Shadcn UI components integrated
✅ AG-UI client connected to backend
✅ Chat interface with message history
✅ Thread creation and management
✅ LocalStorage persistence working
✅ Beautiful Lucide icons for avatars
✅ Responsive layout (mobile + desktop)
✅ Real-time message updates via AG-UI
✅ Error handling and loading states

## Next Steps After Completion

1. Integrate with Backend LangGraph agents
2. Add advanced features (typing indicators, message reactions)
3. Implement authentication (if needed)
4. Add agent selection UI
5. Implement multi-agent visualization

## Notes

- **AG-UI Library**: Use context7 to fetch latest documentation from https://context7.com/ag-ui-protocol/ag-ui
- **Component Library**: Shadcn UI provides ready-to-use, accessible components
- **State Management**: Use React hooks for local state, no need for Redux/Zustand for MVP
- **Persistence**: LocalStorage is sufficient for MVP; migrate to backend database later if needed
- **Backend Contract**: Frontend assumes backend exposes AG-UI protocol endpoints

## References

- [AG-UI Protocol Documentation](https://context7.com/ag-ui-protocol/ag-ui)
- [Shadcn UI Docs](https://ui.shadcn.com)
- [NextJS App Router](https://nextjs.org/docs/app)
- [Lucide React Icons](https://lucide.dev)

---

**Plan created by**: Frontend Agent  
**Status**: Ready for Implementation  
**Estimated Time**: 8-12 hours
