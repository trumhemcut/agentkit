# Frontend Architecture Documentation

## Overview

The AgentKit frontend is a modern NextJS application built with TypeScript, Shadcn UI, and AG-UI protocol for real-time agent communication.

## Technology Stack

- **Framework**: NextJS 14 (App Router)
- **Language**: TypeScript
- **UI Library**: Shadcn UI (built on Radix UI)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Agent Protocol**: AG-UI (Server-Sent Events)
- **State Management**: React Hooks
- **Persistence**: LocalStorage

## Project Structure

```
/frontend
  /app
    layout.tsx          # Root layout with metadata
    page.tsx            # Home page (main chat interface)
    globals.css         # Global styles & Tailwind config
  /components
    Header.tsx          # App header with branding
    Sidebar.tsx         # Thread list sidebar
    Layout.tsx          # Main layout composition
    ChatContainer.tsx   # Main chat interface container
    ChatHistory.tsx     # Message list display
    MessageBubble.tsx   # Individual message component
    ChatInput.tsx       # Message input box
    AvatarIcon.tsx      # User/Agent avatar icons
    /ui                 # Shadcn UI components
      button.tsx
      input.tsx
      textarea.tsx
      card.tsx
      scroll-area.tsx
      avatar.tsx
      separator.tsx
  /hooks
    useChatThreads.ts   # Thread management hook
    useMessages.ts      # Message state hook
    useAGUI.ts          # AG-UI integration hook
  /services
    storage.ts          # LocalStorage service
    agui-client.ts      # AG-UI SSE client
    api.ts              # Backend API client
  /types
    chat.ts             # Chat-related types
    agent.ts            # Agent-related types
    agui.ts             # AG-UI protocol types
  /lib
    utils.ts            # Utility functions
```

## Key Patterns

### 1. Component Architecture

All components follow a consistent pattern:
- Export named functions (not default exports for components)
- Use TypeScript interfaces for props
- Include JSDoc comments for documentation
- Follow "use client" directive for client components

### 2. State Management

State is managed using custom React hooks:
- `useChatThreads`: Manages chat thread CRUD operations
- `useMessages`: Handles message state for current thread
- `useAGUI`: Integrates with backend AG-UI event stream

### 3. Data Persistence

LocalStorage is used for client-side persistence:
- Threads are stored with all messages
- Data is automatically synced on changes
- Services layer abstracts storage operations

### 4. AG-UI Integration

The AG-UI protocol enables real-time agent communication:
- Server-Sent Events (SSE) for streaming
- Event types: RUN_STARTED, TEXT_MESSAGE_CHUNK, RUN_FINISHED, ERROR
- Automatic reconnection handling
- Event listener pattern for flexibility

## Component Documentation

See individual component files:
- [Components Guide](./components.md)
- [Hooks Guide](./hooks.md)
- [Services Guide](./services.md)
- [AG-UI Integration](./agui-integration.md)

## Getting Started

### Development

```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3000

### Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Build

```bash
npm run build
npm start
```

## Backend Integration

The frontend expects the following backend endpoints:

- `POST /api/chat/message` - Send user message
- `GET /api/agent/stream?threadId={id}` - SSE endpoint for AG-UI events

See [Backend Integration Guide](./backend-integration.md) for details.
