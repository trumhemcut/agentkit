# Copilot Instructions for AgentKit

## Project Overview
Multi-agent chat application using **LangGraph** for orchestration and **AG-UI** for agent-frontend protocol communication.

**Stack**: 
- Backend: Python, FastAPI, LangGraph, AG-UI
- Frontend: TypeScript, NextJS, Shadcn UI, AG-UI

## Architecture

### Backend
- **Agent Orchestration**: LangGraph multi-agent workflows 
- **State Management**: LangGraph state graphs with conditional routing
- **LLM Integration**: Ollama provider with `qwen:7b` model (extensible to other providers)
- **API Server**: FastAPI with CORS, streaming SSE endpoints
- **AG-UI Protocol**: Real-time agent stream events to front-end app as JSON stream. 
- **Observability**: LangFuse integration (optional), structured logging
- **Tools**: Search tools, code execution capabilities (Optional)
- See [.github/agents/backend.agent.md](.github/agents/backend.agent.md) for detailed patterns

### Frontend
- **UI Framework**: NextJS + Shadcn UI for modern, accessible component library
- **AG-UI Client**: Receives event streams from backend (RUN_STARTED, TEXT_MESSAGE_CHUNK, RUN_FINISHED, etc.)

- **TypeScript**: Full type safety with proper interfaces
- **Shadcn UI**: Modern, responsive UI design with Shadcn UI components
- **State Management**: React hooks for agent state tracking
- See [.github/agents/frontend.agent.md](.github/agents/frontend.agent.md) for UI patterns


## Development Patterns

### Agent Workflow Design
When building LangGraph agents:
- Inherit from `BaseAgent` class with AG-UI integration
- Define clear state schemas using `AgentState` TypedDict
- Use conditional edges for intelligent routing between agents
- Implement tools as separate classes inheriting from `BaseTool`
- Emit AG-UI events for frontend visibility (THINKING, EXECUTING, COMPLETE, ERROR)
- Support streaming responses through SSE

### LLM Integration
- Use `LLMProviderFactory` to get provider instances
- Default: Ollama with `qwen:7b` model
- Extensible to OpenAI, Anthropic, and other providers
- Configure via `config.py` and environment variables

### Frontend Integration
When building UI components:
- Use Shadcn UI components for consistent, accessible UI design
- Integrate AG-UI client to receive real-time event streams from backend
- Type all agent states and messages with TypeScript interfaces
- Handle SSE events through AG-UI client for real-time updates
- Connect to backend using typed API client in `services/api.ts`
- Use Tailwind CSS with Shadcn UI for styling with responsive design

## Specialized Agents

This project uses specialized chat agents for focused development:

### Implementation Planner (`implementation-planner.agent.md`)
- **Use for**: Creating implementation plans, breaking down features
- **Outputs**: Markdown files in `/.docs/1-implementation-plans/`
- **Coordinates**: Work between Backend and Frontend agents
- **Boundaries**: Does not implement code directly

### Backend Agent (`backend.agent.md`)
- **Use for**: LangGraph workflows, agent nodes, state graphs, routing logic, agent tools, FastAPI endpoints
- **Tech**: Python, LangGraph, FastAPI, Ollama, LangFuse (optional)
- **Virtual Env**: `/.venv`
- **Boundaries**: Does not modify frontend or infrastructure

### Frontend Agent (`frontend.agent.md`)
- **Use for**: AG-UI components, React UI, agent visualization, TypeScript types
- **Tech**: React, TypeScript, NextJS, Shadcn UI, AG-UI, Tailwind CSS
- **Boundaries**: Does not modify backend agent logic or LangGraph workflows

## Key Files
- [agents.md](../agents.md) - Multi-agent architecture overview
- [.github/agents/implementation-planner.agent.md](.github/agents/implementation-planner.agent.md) - Feature planning guide
- [.github/agents/backend.agent.md](.github/agents/backend.agent.md) - LangGraph implementation guide
- [.github/agents/frontend.agent.md](.github/agents/frontend.agent.md) - AG-UI guide
- [.docs/1-implementation-plans/](.docs/1-implementation-plans/) - Feature implementation plans

### When Implementing Features:
1. **Backend**: Design LangGraph workflow, agent nodes, and tools
2. **AG-UI Protocol**: Define communication contract (events, state sync)
3. **Frontend**: Build UI components with AG-UI stream events and Shadcn UI

## Knowledge base
- Refer to .docs/1-implementation-plans/ for implementation plans
- Refer to .docs/2-knowledge-base/ for comprehensive knowledge base

**When you finish, always update the knowledge-base documentation in `/.docs/2-knowledge-base/` to reflect new patterns or components created in a well-organised manner**

**Don't create any other guidance outside of the knowledge-base documentation.**

**always use context7** to fetch latest document and code snippets.