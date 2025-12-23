# System Architecture Overview

**Last Updated**: December 23, 2025  
**Status**: Production

## System Overview

AgentKit is a **multi-agent AI system** that uses **LangGraph** for agent orchestration and **AG-UI protocol** for real-time agent-frontend communication. The system enables building intelligent conversational applications with streaming responses and real-time status updates.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Frontend                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │          NextJS Application (TypeScript)               │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │   Shadcn UI  │  │  AG-UI       │  │   React    │  │  │
│  │  │  Components  │  │  Client      │  │   Hooks    │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  │                                                        │  │
│  │  User Interface with real-time agent communication    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP POST (SSE Stream)
                            │ Accept: text/event-stream
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                         Backend                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │            FastAPI Server (Python)                     │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │   FastAPI    │  │   AG-UI      │  │ LangGraph  │  │  │
│  │  │   Routes     │  │   Protocol   │  │  Agents    │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  │                                                        │  │
│  │  Stream AG-UI events via Server-Sent Events (SSE)    │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                  │
│                            │ LLM API Calls                    │
│                            ▼                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              LLM Provider (Ollama)                     │  │
│  │                    qwen:4b model                       │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Core Technologies

### Backend Stack
- **Python 3.12**: Modern Python with type hints
- **FastAPI**: High-performance async HTTP server
- **LangGraph**: Multi-agent workflow orchestration
- **Ollama**: Local LLM provider (qwen:4b model)
- **AG-UI Protocol SDK**: Official Python SDK for event streaming
- **Pydantic**: Data validation and settings management

### Frontend Stack
- **TypeScript**: Type-safe JavaScript
- **NextJS 14**: React framework with App Router
- **Shadcn UI**: Modern component library (built on Radix UI)
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
- **AG-UI Client**: Event stream processor

## Architecture Layers

### 1. Presentation Layer (Frontend)

**Responsibility**: User interface and interaction

```
Components → Hooks → Services
     ↓         ↓        ↓
  Shadcn     AGUI    Storage
    UI      Client   LocalDB
```

**Key Components**:
- **UI Components**: Shadcn UI-based React components
- **Hooks**: Custom React hooks for state management
  - `useAGUI` - AG-UI event integration
  - `useChatThreads` - Thread management
  - `useMessages` - Message state
- **Services**:
  - `agui-client.ts` - SSE event processor
  - `api.ts` - Backend API client
  - `storage.ts` - LocalStorage persistence

### 2. API Layer (Backend)

**Responsibility**: HTTP endpoints and event streaming

```
FastAPI Routes → Request Validation → Response Streaming
       ↓               ↓                    ↓
   Pydantic        Input DTOs         SSE Events
    Models         Validation         AG-UI Format
```

**Key Endpoints**:
- `POST /api/chat` - Send message, receive SSE stream
- `GET /health` - Health check endpoint

**Features**:
- CORS configuration for frontend access
- SSE streaming with proper headers
- Request validation with Pydantic
- Error handling and logging

### 3. Agent Layer (Backend)

**Responsibility**: AI agent orchestration and execution

```
LangGraph Workflow → Agent Nodes → State Management
        ↓                ↓              ↓
  Conditional       BaseAgent      AgentState
    Routing         Classes        TypedDict
```

**Key Components**:
- **BaseAgent**: Abstract base class for all agents
- **ChatAgent**: Conversational agent implementation
- **State Graphs**: LangGraph workflow definitions
- **Conditional Routing**: Intelligent agent selection

### 4. LLM Integration Layer (Backend)

**Responsibility**: Language model interaction

```
Provider Factory → LLM Provider → Model API
       ↓               ↓             ↓
  Configuration   Ollama Provider  qwen:4b
   Management     Implementation   Inference
```

**Key Components**:
- **Provider Factory**: Unified LLM provider interface
- **Ollama Provider**: Local model integration
- **Configuration**: Environment-based settings

### 5. Protocol Layer (AG-UI)

**Responsibility**: Agent-frontend communication

```
Agent Events → AG-UI Encoder → SSE Stream → Frontend Client
      ↓             ↓              ↓              ↓
Event Types   JSON Format    text/event     Event Parser
 (Python)     (data: {...})    -stream      (TypeScript)
```

**Event Flow**:
1. Agent emits AG-UI events during execution
2. EventEncoder formats events as SSE
3. FastAPI streams events to frontend
4. AG-UI Client parses and dispatches events
5. React components update UI reactively

## Data Flow

### User Message Flow

```
1. User Input
   └─> ChatInput component
       └─> handleSendMessage
           └─> Create user message + runId
               └─> Add to local state
                   └─> Call backend API

2. Backend Processing
   └─> POST /api/chat with messages
       └─> FastAPI route handler
           └─> Initialize LangGraph agent
               └─> Stream AG-UI events

3. Event Streaming
   └─> RUN_STARTED event
   └─> TEXT_MESSAGE_START event
   └─> TEXT_MESSAGE_CONTENT events (streaming)
   └─> TEXT_MESSAGE_END event
   └─> RUN_FINISHED event

4. Frontend Updates
   └─> AG-UI Client receives events
       └─> Event handlers process events
           └─> Update message state
               └─> React re-renders UI
                   └─> User sees streaming response
```

### State Management Flow

```
Frontend State (React)
  ├─> Chat Threads (useChatThreads)
  │   └─> LocalStorage persistence
  ├─> Messages (useMessages)
  │   └─> In-memory + LocalStorage
  └─> AG-UI Connection (useAGUI)
      └─> Event-driven updates

Backend State (LangGraph)
  └─> AgentState (TypedDict)
      ├─> messages: List[BaseMessage]
      ├─> thread_id: str
      ├─> run_id: str
      └─> Custom agent state
```

## Communication Protocols

### HTTP/REST
- **Usage**: Initial message submission
- **Method**: POST /api/chat
- **Format**: JSON request body
- **Response**: SSE stream

### Server-Sent Events (SSE)
- **Usage**: Real-time agent event streaming
- **Direction**: Server → Client (unidirectional)
- **Format**: `data: {...}\n\n` (AG-UI events)
- **Content-Type**: `text/event-stream`

### AG-UI Protocol
- **Events**: Typed event classes (Pydantic on backend, TypeScript on frontend)
- **Lifecycle**: RUN_STARTED → ... → RUN_FINISHED/ERROR
- **Messages**: START → CONTENT (chunks) → END
- **State**: Thread ID + Run ID for correlation

## Deployment Architecture

### Development
```
Frontend:  localhost:3000 (NextJS dev server)
Backend:   localhost:8000 (uvicorn)
LLM:       localhost:11434 (Ollama)
```

### Production (Planned)
```
Frontend:  Vercel/Static hosting
Backend:   Container (Docker) + Cloud hosting
LLM:       Self-hosted Ollama or Cloud API
```

## Key Design Patterns

### 1. Factory Pattern
- `LLMProviderFactory` - Create LLM provider instances
- Extensible to multiple providers (OpenAI, Anthropic, etc.)

### 2. Observer Pattern
- AG-UI event system
- Frontend subscribes to event types
- Reactive UI updates

### 3. State Machine
- LangGraph workflows
- Conditional routing between agents
- Type-safe state transitions

### 4. Repository Pattern
- `storage.ts` - Abstract storage operations
- LocalStorage implementation
- Easy to swap for API-based storage

### 5. Adapter Pattern
- AG-UI Client - Adapts SSE to React state
- Provider wrappers - Unified LLM interface

## Security Considerations

### Current Implementation
- CORS enabled for frontend origin
- Local development setup
- No authentication (development mode)

### Production Requirements
- [ ] Authentication (JWT, OAuth, etc.)
- [ ] API rate limiting
- [ ] Input sanitization
- [ ] HTTPS/TLS encryption
- [ ] Environment variable protection
- [ ] Secret management

## Performance Optimization

### Backend
- **Async/Await**: FastAPI async endpoints
- **Streaming**: SSE for incremental responses
- **Connection Pooling**: Reuse LLM connections

### Frontend
- **Code Splitting**: NextJS automatic splitting
- **Lazy Loading**: Dynamic imports for routes
- **Local Caching**: LocalStorage for threads/messages
- **Debouncing**: Input debouncing for API calls

## Monitoring & Observability

### Logging
- **Backend**: Python logging with structured logs
- **Frontend**: Console logging for development

### Optional Integrations
- **LangFuse**: LLM call tracing and monitoring
- **Metrics**: Performance tracking
- **Error Tracking**: Sentry or similar

## Scalability Considerations

### Horizontal Scaling
- FastAPI supports multiple workers
- Stateless agent execution
- Shared storage for persistence

### Vertical Scaling
- LLM model size vs. performance tradeoff
- Agent complexity impacts latency
- Streaming reduces perceived latency

## Extension Points

### Backend
1. **New Agents**: Extend BaseAgent class
2. **New LLM Providers**: Implement provider interface
3. **Custom Tools**: Add to agent tool registry
4. **Workflow Customization**: Define new LangGraph workflows

### Frontend
1. **New Components**: Add to components directory
2. **Custom Hooks**: Create domain-specific hooks
3. **Theme Customization**: Modify Tailwind config
4. **New Views**: Add NextJS app routes

## Related Documentation

- [Backend Architecture Details](backend-architecture.md)
- [Frontend Architecture Details](frontend-architecture.md)
- [AG-UI Protocol Specification](../agui-protocol/README.md)
- [Backend Implementation](../backend/README.md)
- [Frontend Implementation](../frontend/README.md)

---

*This document provides a high-level overview. See detailed documentation for specific implementations.*
