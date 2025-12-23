# Knowledge Base

**Last Updated**: December 23, 2025

## Overview

This knowledge base contains comprehensive documentation for the AgentKit multi-agent system. The project uses **LangGraph** for agent orchestration and **AG-UI** protocol for real-time agent-frontend communication.

## 📁 Documentation Structure

```
2-knowledge-base/
├── README.md                    # This file - Knowledge base index
├── architecture/                # System architecture & design
│   ├── overview.md             # High-level system architecture
│   ├── backend-architecture.md # Backend structure & patterns
│   └── frontend-architecture.md# Frontend structure & patterns
├── agui-protocol/              # AG-UI Protocol documentation
│   ├── README.md               # Protocol overview
│   ├── protocol-spec.md        # Event types & streaming spec
│   ├── backend-integration.md  # Backend AG-UI implementation
│   └── frontend-integration.md # Frontend AG-UI client
├── backend/                    # Backend implementation docs
│   ├── README.md               # Backend overview
│   ├── agents/                 # Agent implementations
│   │   ├── base-agent.md      # BaseAgent class & patterns
│   │   └── chat-agent.md      # ChatAgent implementation
│   ├── api/                    # API documentation
│   │   ├── routes.md          # FastAPI endpoints
│   │   └── models.md          # Pydantic models
│   ├── llm/                    # LLM provider docs
│   │   ├── providers.md       # Provider implementations
│   │   └── ollama.md          # Ollama configuration
│   └── graphs/                 # LangGraph workflows
│       └── chat-graph.md      # Chat workflow design
└── frontend/                   # Frontend implementation docs
    ├── README.md               # Frontend overview
    ├── components/             # UI Components
    │   ├── overview.md        # Component architecture
    │   ├── chat-components.md # Chat UI components
    │   └── ui-library.md      # Shadcn UI usage
    ├── hooks/                  # React hooks
    │   ├── overview.md        # Hook patterns
    │   ├── useAGUI.md         # AG-UI integration hook
    │   ├── useChatThreads.md  # Thread management
    │   └── useMessages.md     # Message state
    └── services/               # Frontend services
        ├── overview.md        # Service layer
        ├── agui-client.md     # SSE client
        ├── api.md             # Backend API client
        └── storage.md         # LocalStorage service
```

## 🎯 Quick Navigation

### Getting Started
- [System Architecture Overview](architecture/overview.md) - Start here for high-level understanding
- [Backend Architecture](architecture/backend-architecture.md) - Backend design patterns
- [Frontend Architecture](architecture/frontend-architecture.md) - Frontend design patterns

### AG-UI Protocol
- [AG-UI Protocol Overview](agui-protocol/README.md) - Real-time agent communication
- [Protocol Specification](agui-protocol/protocol-spec.md) - Event types & streaming
- [Backend Integration](agui-protocol/backend-integration.md) - SSE streaming implementation
- [Frontend Integration](agui-protocol/frontend-integration.md) - AG-UI client usage

### Backend Development
- [Backend Overview](backend/README.md) - Backend structure & getting started
- [Agent Development](backend/agents/base-agent.md) - Building LangGraph agents
- [API Routes](backend/api/routes.md) - FastAPI endpoints
- [LLM Providers](backend/llm/providers.md) - LLM integration patterns

### Frontend Development
- [Frontend Overview](frontend/README.md) - Frontend structure & getting started
- [Component Library](frontend/components/overview.md) - UI component architecture
- [AG-UI Hooks](frontend/hooks/useAGUI.md) - Real-time agent integration
- [Services](frontend/services/overview.md) - Frontend service layer

## 🔑 Key Concepts

### Multi-Agent System
- **LangGraph**: Orchestrates agent workflows with state graphs and conditional routing
- **BaseAgent**: Abstract base class for all agents with AG-UI integration
- **State Management**: Typed state schemas using TypedDict for type safety

### AG-UI Protocol
- **Server-Sent Events (SSE)**: Real-time streaming from backend to frontend
- **Event Types**: RUN_STARTED, TEXT_MESSAGE_CHUNK, THINKING, EXECUTING, RUN_FINISHED, ERROR
- **State Synchronization**: Bidirectional communication between agents and UI

### Technology Stack

**Backend**
- Python 3.12
- LangGraph (agent orchestration)
- FastAPI (HTTP/SSE server)
- Ollama (LLM provider - qwen:7b)
- Pydantic (validation & settings)

**Frontend**
- TypeScript
- NextJS 14 (App Router)
- Shadcn UI (component library)
- AG-UI (agent protocol client)
- Tailwind CSS (styling)

## 📚 Documentation Standards

### File Organization
- Each major component has its own directory with README.md
- Related documentation is grouped together
- Cross-references use relative links

### Content Structure
- **Overview**: High-level description and purpose
- **Architecture**: Design patterns and structure
- **Implementation**: Code examples and usage patterns
- **API Reference**: Function signatures and parameters
- **Examples**: Real-world usage scenarios

### Maintenance
- Update documentation when implementing new features
- Date stamp major updates
- Keep examples synchronized with code
- Remove outdated information promptly

## 🔄 Contributing to Knowledge Base

When adding new documentation:

1. **Identify the correct location** in the directory structure
2. **Follow the existing format** for consistency
3. **Include code examples** where applicable
4. **Update this README** if adding new top-level sections
5. **Cross-reference** related documents

## 📝 Document Templates

### Component Documentation Template
```markdown
# Component Name

**Status**: Implemented/In Progress/Planned
**Last Updated**: YYYY-MM-DD

## Overview
Brief description of the component's purpose

## Architecture
Design patterns and structure

## Implementation
Code examples and usage

## API Reference
Function signatures and parameters

## Examples
Real-world usage scenarios

## Related Documentation
- [Link to related docs]
```

## 🎓 Learning Path

### For New Developers
1. Read [System Architecture Overview](architecture/overview.md)
2. Understand [AG-UI Protocol](agui-protocol/README.md)
3. Explore [Backend Architecture](architecture/backend-architecture.md)
4. Review [Frontend Architecture](architecture/frontend-architecture.md)
5. Follow implementation guides for specific areas

### For Backend Development
1. [Backend Overview](backend/README.md)
2. [BaseAgent Patterns](backend/agents/base-agent.md)
3. [LangGraph Workflows](backend/graphs/chat-graph.md)
4. [API Implementation](backend/api/routes.md)

### For Frontend Development
1. [Frontend Overview](frontend/README.md)
2. [AG-UI Integration](frontend/hooks/useAGUI.md)
3. [Component Architecture](frontend/components/overview.md)
4. [Service Layer](frontend/services/overview.md)

---

*This knowledge base is actively maintained. Last major update: December 23, 2025*
