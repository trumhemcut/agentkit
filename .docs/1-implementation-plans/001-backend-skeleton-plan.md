# Implementation Plan: Backend Skeleton for Agentic AI Solution

**Requirement**: Build the backend skeleton for Agentic AI solution using LangGraph and AG-UI protocol
**Date**: December 23, 2025
**Status**: Planning

## Overview

Build a Python-based backend skeleton that implements a simple chat agent with streaming capabilities using LangGraph for orchestration and AG-UI protocol for agent-frontend communication.

## Architecture Components

### 1. Core Technologies
- **LangGraph**: Multi-agent workflow orchestration framework
- **AG-UI Protocol**: Real-time agent-frontend communication via SSE streaming
- **FastAPI**: HTTP server with streaming endpoints
- **Ollama**: LLM provider with `qwen:4b` model
- **Python**: Backend implementation language

### 2. Project Structure

```
/backend
  /agents          # Agent implementations
    __init__.py
    base_agent.py  # BaseAgent with AG-UI integration
    chat_agent.py  # Simple streaming chat agent
  /api             # API endpoints
    __init__.py
    routes.py      # FastAPI route handlers
    models.py      # Request/response models
  /graphs          # LangGraph workflow definitions
    __init__.py
    chat_graph.py  # Chat agent state graph
  /llm             # LLM provider integrations
    __init__.py
    provider_factory.py
    ollama_provider.py
  /protocols       # AG-UI protocol implementation
    __init__.py
    event_encoder.py   # AG-UI event encoding
    event_types.py     # AG-UI event type definitions
  /observability   # Logging and monitoring (optional)
    __init__.py
    logger.py
  main.py          # FastAPI application entry point
  config.py        # Configuration management
  requirements.txt # Python dependencies
  README.md        # Documentation
```

## Implementation Steps

### Step 1: Environment Setup

**Tasks**:
- Create Python virtual environment at `./.venv`
- Create `requirements.txt` with core dependencies:
  ```
  fastapi==0.115.0
  uvicorn[standard]==0.32.0
  pydantic==2.9.0
  langgraph==0.2.74
  langchain-core==0.3.0
  langchain-ollama==0.2.0
  ag-ui-core==0.1.0
  ag-ui-encoder==0.1.0
  python-dotenv==1.0.0
  ```
- Create project folder structure
- Initialize Git repository

**Files to Create**:
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/.gitignore`

---

### Step 2: Configuration Management

**Tasks**:
- Create configuration system for environment variables
- Set up Ollama provider configuration
- Define server settings (host, port, CORS)

**Files to Create**:
- `backend/config.py`:
  ```python
  import os
  from pydantic_settings import BaseSettings
  
  class Settings(BaseSettings):
      # Server settings
      HOST: str = "0.0.0.0"
      PORT: int = 8000
      DEBUG: bool = True
      
      # LLM settings
      OLLAMA_BASE_URL: str = "http://localhost:11434"
      OLLAMA_MODEL: str = "qwen:4b"
      
      # CORS settings
      CORS_ORIGINS: list = ["http://localhost:3000"]
      
      class Config:
          env_file = ".env"
  
  settings = Settings()
  ```

---

### Step 3: AG-UI Protocol Implementation

**Tasks**:
- Implement AG-UI event type definitions
- Create EventEncoder for SSE streaming
- Define AG-UI event models

**Files to Create**:
- `backend/protocols/__init__.py`
- `backend/protocols/event_types.py`:
  ```python
  from enum import Enum
  
  class EventType(str, Enum):
      RUN_STARTED = "RUN_STARTED"
      RUN_FINISHED = "RUN_FINISHED"
      RUN_ERROR = "RUN_ERROR"
      TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
      TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
      TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
  ```

- `backend/protocols/event_encoder.py`:
  ```python
  import json
  from typing import Dict, Any
  
  class EventEncoder:
      def __init__(self, accept: str = None):
          self.accept = accept or "text/event-stream"
      
      def encode(self, event: Dict[str, Any]) -> str:
          """Encode event as SSE format"""
          event_data = json.dumps(event)
          return f"data: {event_data}\n\n"
      
      def get_content_type(self) -> str:
          return "text/event-stream"
  ```

**Reference Documentation**:
- AG-UI Protocol Events: https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/concepts/events.mdx
- EventEncoder Usage: https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/sdk/python/encoder/overview.mdx

---

### Step 4: LLM Provider Integration

**Tasks**:
- Create provider factory pattern
- Implement Ollama provider with `qwen:4b` model
- Set up streaming support

**Files to Create**:
- `backend/llm/__init__.py`
- `backend/llm/ollama_provider.py`:
  ```python
  from langchain_ollama import ChatOllama
  from backend.config import settings
  
  class OllamaProvider:
      def __init__(self):
          self.model = ChatOllama(
              base_url=settings.OLLAMA_BASE_URL,
              model=settings.OLLAMA_MODEL,
              streaming=True
          )
      
      def get_model(self):
          return self.model
  ```

- `backend/llm/provider_factory.py`:
  ```python
  from backend.llm.ollama_provider import OllamaProvider
  
  class LLMProviderFactory:
      @staticmethod
      def get_provider(provider_type: str = "ollama"):
          if provider_type == "ollama":
              return OllamaProvider()
          raise ValueError(f"Unknown provider: {provider_type}")
  ```

---

### Step 5: LangGraph Chat Agent Implementation

**Tasks**:
- Define agent state schema using TypedDict
- Create BaseAgent class with AG-UI integration
- Implement simple ChatAgent with streaming
- Build LangGraph state graph for chat flow

**Files to Create**:
- `backend/agents/__init__.py`
- `backend/agents/base_agent.py`:
  ```python
  from typing import TypedDict, Annotated
  from abc import ABC, abstractmethod
  
  class AgentState(TypedDict):
      messages: list[dict]
      thread_id: str
      run_id: str
  
  class BaseAgent(ABC):
      @abstractmethod
      async def run(self, state: AgentState):
          """Execute agent logic"""
          pass
  ```

- `backend/agents/chat_agent.py`:
  ```python
  import uuid
  from typing import AsyncGenerator
  from backend.agents.base_agent import BaseAgent, AgentState
  from backend.llm.provider_factory import LLMProviderFactory
  from backend.protocols.event_types import EventType
  
  class ChatAgent(BaseAgent):
      def __init__(self):
          provider = LLMProviderFactory.get_provider("ollama")
          self.llm = provider.get_model()
      
      async def run(self, state: AgentState) -> AsyncGenerator:
          messages = state["messages"]
          message_id = str(uuid.uuid4())
          
          # Start message event
          yield {
              "type": EventType.TEXT_MESSAGE_START,
              "messageId": message_id,
              "role": "assistant"
          }
          
          # Stream LLM response
          async for chunk in self.llm.astream(messages):
              content = chunk.content
              if content:
                  yield {
                      "type": EventType.TEXT_MESSAGE_CONTENT,
                      "messageId": message_id,
                      "delta": content
                  }
          
          # End message event
          yield {
              "type": EventType.TEXT_MESSAGE_END,
              "messageId": message_id
          }
  ```

- `backend/graphs/__init__.py`
- `backend/graphs/chat_graph.py`:
  ```python
  from langgraph.graph import StateGraph, START, END
  from backend.agents.base_agent import AgentState
  from backend.agents.chat_agent import ChatAgent
  
  def create_chat_graph():
      """Create LangGraph state graph for chat agent"""
      workflow = StateGraph(AgentState)
      
      chat_agent = ChatAgent()
      
      # Add agent node
      workflow.add_node("chat", chat_agent.run)
      
      # Define graph flow
      workflow.add_edge(START, "chat")
      workflow.add_edge("chat", END)
      
      return workflow.compile()
  ```

**Reference Documentation**:
- LangGraph Streaming: https://github.com/langchain-ai/langgraph/blob/main/docs/docs/how-tos/streaming.md
- LangGraph State Graphs: https://github.com/langchain-ai/langgraph

---

### Step 6: FastAPI Server Implementation

**Tasks**:
- Create FastAPI application with CORS
- Implement SSE streaming endpoint
- Integrate AG-UI protocol
- Connect LangGraph chat agent

**Files to Create**:
- `backend/api/__init__.py`
- `backend/api/models.py`:
  ```python
  from pydantic import BaseModel, Field
  from typing import List, Dict, Optional
  
  class Message(BaseModel):
      role: str
      content: str
  
  class RunAgentInput(BaseModel):
      thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
      run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
      messages: List[Message]
  ```

- `backend/api/routes.py`:
  ```python
  import uuid
  from fastapi import APIRouter, Request
  from fastapi.responses import StreamingResponse
  from backend.api.models import RunAgentInput
  from backend.protocols.event_encoder import EventEncoder
  from backend.protocols.event_types import EventType
  from backend.graphs.chat_graph import create_chat_graph
  
  router = APIRouter()
  
  @router.post("/chat")
  async def chat_endpoint(input_data: RunAgentInput, request: Request):
      """AG-UI compliant chat endpoint with SSE streaming"""
      accept_header = request.headers.get("accept")
      encoder = EventEncoder(accept=accept_header)
      
      async def event_generator():
          # Send RUN_STARTED event
          yield encoder.encode({
              "type": EventType.RUN_STARTED,
              "threadId": input_data.thread_id,
              "runId": input_data.run_id
          })
          
          try:
              # Create and run LangGraph chat agent
              graph = create_chat_graph()
              
              state = {
                  "messages": [msg.dict() for msg in input_data.messages],
                  "thread_id": input_data.thread_id,
                  "run_id": input_data.run_id
              }
              
              # Stream agent events
              async for event in graph.astream(state):
                  yield encoder.encode(event)
              
              # Send RUN_FINISHED event
              yield encoder.encode({
                  "type": EventType.RUN_FINISHED,
                  "threadId": input_data.thread_id,
                  "runId": input_data.run_id
              })
          
          except Exception as e:
              # Send RUN_ERROR event
              yield encoder.encode({
                  "type": EventType.RUN_ERROR,
                  "threadId": input_data.thread_id,
                  "runId": input_data.run_id,
                  "error": str(e)
              })
      
      return StreamingResponse(
          event_generator(),
          media_type=encoder.get_content_type()
      )
  ```

- `backend/main.py`:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from backend.api.routes import router
  from backend.config import settings
  
  app = FastAPI(title="AgentKit Backend")
  
  # Configure CORS
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.CORS_ORIGINS,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  
  # Register routes
  app.include_router(router, prefix="/api")
  
  @app.get("/health")
  async def health_check():
      return {"status": "healthy"}
  
  if __name__ == "__main__":
      import uvicorn
      uvicorn.run(
          "backend.main:app",
          host=settings.HOST,
          port=settings.PORT,
          reload=settings.DEBUG
      )
  ```

**Reference Documentation**:
- FastAPI SSE Streaming: https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/quickstart/server.mdx
- AG-UI Python Server Example: https://github.com/ag-ui-protocol/ag-ui

---

### Step 7: Testing & Documentation

**Tasks**:
- Create basic test structure
- Add README with setup instructions
- Document API endpoints
- Create example usage scripts

**Files to Create**:
- `backend/README.md`:
  ```markdown
  # AgentKit Backend
  
  ## Setup
  
  1. Create virtual environment:
     ```bash
     python -m venv .venv
     source .venv/bin/activate  # Linux/Mac
     .venv\Scripts\activate     # Windows
     ```
  
  2. Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
  
  3. Configure environment:
     ```bash
     cp .env.example .env
     # Edit .env with your settings
     ```
  
  4. Ensure Ollama is running:
     ```bash
     ollama serve
     ollama pull qwen:4b
     ```
  
  5. Run server:
     ```bash
     python -m backend.main
     ```
  
  ## API Endpoints
  
  ### POST /api/chat
  Chat with agent using AG-UI protocol
  
  **Request Body**:
  ```json
  {
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }
  ```
  
  **Response**: SSE stream with AG-UI events
  
  ### GET /health
  Health check endpoint
  ```

- `backend/.env.example`:
  ```
  HOST=0.0.0.0
  PORT=8000
  DEBUG=True
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=qwen:4b
  CORS_ORIGINS=["http://localhost:3000"]
  ```

---

## Dependencies

### Python Packages
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.0
pydantic-settings==2.5.0
langgraph==0.2.74
langchain-core==0.3.0
langchain-ollama==0.2.0
ag-ui-core==0.1.0
ag-ui-encoder==0.1.0
python-dotenv==1.0.0
```

### External Services
- **Ollama**: Local LLM provider (must be installed and running)
  - Model: `qwen:4b` (must be pulled)

---

## Testing Strategy

### Manual Testing
1. Start Ollama service
2. Run backend server
3. Test `/health` endpoint
4. Test `/api/chat` endpoint with curl:
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{"messages":[{"role":"user","content":"Hello!"}]}'
   ```

### Validation Checklist
- [ ] Virtual environment created at `./.venv`
- [ ] All dependencies installed
- [ ] Ollama running with `qwen:4b` model
- [ ] Server starts without errors
- [ ] Health check returns 200
- [ ] Chat endpoint streams SSE events
- [ ] AG-UI events follow protocol format
- [ ] Messages stream chunk by chunk
- [ ] CORS headers configured correctly

---

## Success Criteria

1. **Backend skeleton is functional**:
   - FastAPI server runs on configured port
   - SSE streaming endpoint works
   - CORS properly configured

2. **AG-UI protocol implemented**:
   - Events follow AG-UI specification
   - RUN_STARTED, TEXT_MESSAGE_*, RUN_FINISHED events emit correctly
   - EventEncoder formats events as SSE

3. **LangGraph integration working**:
   - State graph compiles successfully
   - Agent executes within graph flow
   - State management works correctly

4. **Simple chat agent functional**:
   - Receives user messages
   - Streams responses chunk by chunk
   - Integrates with Ollama `qwen:4b` model
   - No tools implemented (as per requirement)

5. **Code quality**:
   - Clean project structure
   - Type hints used throughout
   - Configuration externalized
   - README documentation complete

---

## Future Extensions (Out of Scope)

These are NOT part of the current implementation but can be added later:
- Agent tools integration
- LangFuse observability
- Multi-agent workflows
- Authentication/authorization
- Rate limiting
- Vector database integration
- Advanced error handling
- Unit/integration tests
- Docker containerization

---

## References

### AG-UI Protocol
- Protocol Documentation: https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/concepts/events.mdx
- Python SDK: https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/sdk/python/encoder/overview.mdx
- Server Implementation: https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/quickstart/server.mdx

### LangGraph
- Official Docs: https://github.com/langchain-ai/langgraph
- Streaming Guide: https://github.com/langchain-ai/langgraph/blob/main/docs/docs/how-tos/streaming.md
- State Graphs: https://github.com/langchain-ai/langgraph

### FastAPI
- Official Docs: https://fastapi.tiangolo.com/
- Streaming Response: https://fastapi.tiangolo.com/advanced/custom-response/

---

## Implementation Notes

- Use **context7** for fetching latest documentation during implementation
- Follow the folder structure exactly as specified
- Ensure `./.venv` is used for virtual environment
- All async operations should use proper async/await patterns
- Keep the initial implementation simple - no tools, just chat
- Focus on streaming functionality - chunk-by-chunk response delivery
- AG-UI protocol compliance is critical for frontend integration
