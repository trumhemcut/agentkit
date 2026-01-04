# Frontend Documentation

**Last Updated**: December 23, 2025

## Overview

The frontend is a **NextJS 14 application** built with **TypeScript** and **Shadcn UI**. It integrates with the backend using the **AG-UI protocol** for real-time agent communication via Server-Sent Events.

## Quick Links

- [Architecture Overview](../architecture/frontend-architecture.md) - Detailed frontend architecture
- [Components](components/overview.md) - UI component documentation
- [Hooks](hooks/overview.md) - React hooks for state management
- [Services](services/overview.md) - API and storage services
- [Database Persistence](persistence/database-integration.md) - Server-side persistence (NEW)
- [AG-UI Integration](hooks/useAGUI.md) - Real-time agent events
- [A2UI Integration](a2ui-integration.md) - Declarative UI rendering from agents
- [A2UI Quick Reference](a2ui-quick-reference.md) - Quick start guide for A2UI

## Project Structure

```
/frontend
├── app/                # NextJS App Router
│   ├── layout.tsx     # Root layout
│   ├── page.tsx       # Home page (chat interface)
│   └── globals.css    # Global styles
├── components/         # UI Components
│   ├── Header.tsx     # App header
│   ├── Sidebar.tsx    # Thread list sidebar
│   ├── Layout.tsx     # Main layout composition
│   ├── ChatContainer.tsx   # Chat interface
│   ├── ChatHistory.tsx     # Message list
│   ├── MessageBubble.tsx   # Message component
│   ├── ChatInput.tsx       # Input box
│   ├── AvatarIcon.tsx      # Avatar icons
│   ├── A2UI/               # A2UI Components (NEW)
│   │   ├── A2UIRenderer.tsx      # Surface renderer
│   │   └── components/           # A2UI component library
│   │       ├── A2UICheckbox.tsx  # Checkbox component
│   │       └── ...               # More components
│   └── ui/            # Shadcn UI components
├── hooks/              # Custom React hooks
│   ├── useChatThreads.ts   # Thread management
│   ├── useMessages.ts      # Message state
│   ├── useAGUI.ts          # AG-UI integration
│   └── useA2UIEvents.ts    # A2UI event processing (NEW)
├── services/           # Service layer
│   ├── storage.ts          # LocalStorage with server sync
│   ├── agui-client.ts      # SSE client
│   └── api.ts              # Backend API (includes DB endpoints)
├── stores/             # Zustand stores
│   ├── modelStore.ts       # Model selection
│   ├── agentStore.ts       # Agent selection
│   └── a2uiStore.ts        # A2UI state (NEW)
├── types/              # TypeScript types
│   ├── agent.ts            # Agent types
│   ├── agui.ts             # AG-UI event types
│   ├── a2ui.ts             # A2UI types (NEW)
│   ├── database.ts         # Database persistence types (NEW)
│   └── chat.ts             # Chat types
└── lib/                # Utilities
    └── utils.ts            # Helper functions
```

## Core Components

### 1. Components (`/components`)

**Purpose**: UI building blocks

**Key Components**:
- [`ChatContainer`](components/overview.md#chatcontainer) - Main chat interface
- [`ChatHistory`](components/overview.md#chathistory) - Message list with streaming
- [`MessageBubble`](components/overview.md#messagebubble) - Individual message display
- [`ChatInput`](components/overview.md#chatinput) - Message input with send
- [`Sidebar`](components/overview.md#sidebar) - Thread navigation
- [`Header`](components/overview.md#header) - App branding
- [`ui/`](components/overview.md#shadcn-ui) - Shadcn UI primitives

### 2. Hooks (`/hooks`)

**Purpose**: Reusable state management logic

**Key Hooks**:
- [`useAGUI`](hooks/useAGUI.md) - AG-UI event integration
  - Event subscription
  - Connection state
  - Real-time updates

- [`useA2UIEvents`](a2ui-integration.md#event-processing) - A2UI event processing (NEW)
  - Process A2UI messages from SSE stream
  - Update A2UI store with surface/data changes
  - Handle surface lifecycle
  
- [`useChatThreads`](hooks/overview.md#usechatthreads) - Thread management
  - Create/delete threads
  - Thread persistence
  - Active thread selection
  
- [`useMessages`](hooks/overview.md#usemessages) - Message state
  - Add/update messages
  - Streaming message accumulation
  - Message persistence

### 3. Services (`/services`)

**Purpose**: External integrations and data persistence

**Key Services**:
- [`agui-client.ts`](services/overview.md#agui-client) - SSE event processor
  - Parse AG-UI events
  - Event dispatching
  - Connection management
  
- [`api.ts`](services/api.md) - Backend API client
  - HTTP requests
  - SSE streaming
  - Database persistence endpoints (NEW)
  - Error handling
  
- [`storage.ts`](services/overview.md#storage) - LocalStorage with server sync
  - Thread persistence (local + server)
  - Message storage (local + server)
  - Background sync (Phase 1)
  - Data serialization

### 4. Types (`/types`)

**Purpose**: TypeScript type definitions

**Key Types**:
- `agui.ts` - AG-UI event types
- `chat.ts` - Message and Thread types
- `agent.ts` - Agent-related types

## Development Workflow

### Setup

```bash
# Install dependencies
cd frontend
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running

```bash
# Start development server
npm run dev

# Frontend runs at http://localhost:3000
```

### Building

```bash
# Production build
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint
```

## Key Patterns

### 1. Component Architecture
- Named exports for components
- TypeScript interfaces for props
- "use client" directive for interactive components
- Composition over inheritance

### 2. State Management
- Custom hooks for domain logic
- LocalStorage for persistence
- React state for UI state
- Event-driven updates from AG-UI

### 3. AG-UI Integration
```typescript
// Subscribe to events
const { on } = useAGUI();

useEffect(() => {
  const unsubscribe = on('TEXT_MESSAGE_CONTENT', (event) => {
    // Handle streaming content
  });
  
  return unsubscribe; // Cleanup
}, []);
```

### 4. Error Handling
- Try/catch in async operations
- Error boundaries for React errors
- User-friendly error messages
- Graceful degradation

## Common Tasks

### Adding a New Component

1. Create component file:
```typescript
// components/MyComponent.tsx
"use client";

interface MyComponentProps {
  prop: string;
}

export function MyComponent({ prop }: MyComponentProps) {
  return <div>{prop}</div>;
}
```

2. Add to parent component
3. Document in components/overview.md

### Adding a New Hook

1. Create hook file:
```typescript
// hooks/useMyHook.ts
export function useMyHook() {
  const [state, setState] = useState();
  
  return {
    state,
    setState
  };
}
```

2. Use in components
3. Document in hooks/overview.md

### Adding a New Service

1. Create service file:
```typescript
// services/my-service.ts
export class MyService {
  static async doSomething() {
    // Implementation
  }
}
```

2. Import and use in components/hooks
3. Document in services/overview.md

## Best Practices

### Component Development
- ✅ Keep components focused and small
- ✅ Use TypeScript for type safety
- ✅ Extract reusable logic into hooks
- ✅ Use Shadcn UI components when possible
- ✅ Follow accessibility guidelines

### State Management
- ✅ Use custom hooks for complex state
- ✅ Keep state as local as possible
- ✅ Persist important data to LocalStorage
- ✅ Clean up effects and subscriptions

### AG-UI Integration
- ✅ Subscribe to specific event types
- ✅ Unsubscribe on component unmount
- ✅ Handle connection errors gracefully
- ✅ Show loading states during streaming

### Performance
- ✅ Use React.memo for expensive renders
- ✅ Debounce user input
- ✅ Lazy load routes with dynamic imports
- ✅ Optimize images with NextJS Image

## Troubleshooting

### Common Issues

**Issue**: SSE connection fails
```typescript
// Solution: Check backend URL in .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Issue**: Messages not persisting
```typescript
// Solution: Check LocalStorage is enabled
// Check browser console for storage errors
```

**Issue**: Type errors
```bash
# Solution: Run type check
npm run type-check
# Fix reported errors
```

**Issue**: Hydration errors
```typescript
// Solution: Ensure "use client" directive on interactive components
"use client";
```

## Related Documentation

- [System Architecture](../architecture/overview.md) - High-level system design
- [AG-UI Protocol](../agui-protocol/README.md) - Event streaming protocol
- [Backend Integration](../backend/README.md) - Backend API documentation

## Resources

- [NextJS Documentation](https://nextjs.org/docs)
- [Shadcn UI](https://ui.shadcn.com/)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Documentation](https://react.dev/)

---

*For detailed implementation guides, see subdirectories: components/, hooks/, services/*
