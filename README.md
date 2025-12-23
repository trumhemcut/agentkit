# AgentKit

A modern multi-agent AI assistant built with **LangGraph** for orchestration and **AG-UI** for real-time agent-frontend communication.

## 🚀 Features

- **Multi-Agent Orchestration**: Powered by LangGraph for complex workflow management
- **Real-time Streaming**: AG-UI protocol for live agent communication
- **Modern UI**: NextJS + Shadcn UI for a beautiful, responsive interface
- **Flexible LLM Integration**: Default Ollama support, extensible to OpenAI, Anthropic, and more
- **Thread Management**: Create and manage multiple conversation threads
- **Type-Safe**: Full TypeScript support on frontend, Python type hints on backend
- **Observability**: Optional LangFuse integration for monitoring and debugging
- **Local Storage**: Client-side persistence for threads and messages

## 📋 Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **Ollama** (for local LLM inference)

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI with streaming SSE endpoints
- **Agent Orchestration**: LangGraph multi-agent workflows
- **State Management**: LangGraph state graphs with conditional routing
- **LLM Provider**: Ollama (`qwen:7b` model by default)
- **Protocol**: AG-UI for real-time event streaming
- **Observability**: LangFuse integration (optional)

### Frontend
- **Framework**: NextJS 14 with App Router
- **UI Library**: Shadcn UI + Tailwind CSS
- **Type Safety**: Full TypeScript implementation
- **State Management**: React hooks
- **Protocol**: AG-UI client for event stream handling
- **Storage**: LocalStorage for thread persistence

### Communication Flow

```
User Input → Frontend (AG-UI Client) → Backend (FastAPI) → LangGraph Agent
                                                                    ↓
                                                                LLM (Ollama)
                                                                    ↓
User Display ← Frontend ← AG-UI Events (SSE Stream) ← Backend ← Response
```

## 🛠️ Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional)
cp .env.example .env
# Edit .env with your settings

# Ensure Ollama is running
ollama serve
ollama pull qwen:7b

# Start backend server
python -m backend.main
```

Backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
agenkit/
├── backend/                 # Python backend
│   ├── agents/             # Agent implementations
│   │   ├── base_agent.py   # Base agent class with AG-UI integration
│   │   └── chat_agent.py   # Chat agent implementation
│   ├── api/                # API layer
│   │   ├── models.py       # Pydantic models
│   │   └── routes.py       # FastAPI endpoints
│   ├── graphs/             # LangGraph workflows
│   │   └── chat_graph.py   # Chat workflow definition
│   ├── llm/                # LLM provider integrations
│   │   ├── ollama_provider.py
│   │   └── provider_factory.py
│   ├── protocols/          # AG-UI protocol implementation
│   │   ├── event_encoder.py
│   │   └── event_types.py
│   ├── config.py           # Configuration management
│   └── main.py             # FastAPI application entry
│
├── frontend/               # NextJS frontend
│   ├── app/               # NextJS app directory
│   │   ├── globals.css    # Global styles
│   │   ├── layout.tsx     # Root layout
│   │   └── page.tsx       # Home page
│   ├── components/        # React components
│   │   ├── ChatContainer.tsx
│   │   ├── ChatHistory.tsx
│   │   ├── ChatInput.tsx
│   │   ├── Header.tsx
│   │   ├── Layout.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── Sidebar.tsx
│   │   └── ui/           # Shadcn UI components
│   ├── hooks/            # Custom React hooks
│   │   ├── useAGUI.ts    # AG-UI integration hook
│   │   ├── useChatThreads.ts
│   │   └── useMessages.ts
│   ├── services/         # API and storage services
│   │   ├── agui-client.ts
│   │   ├── api.ts
│   │   └── storage.ts
│   └── types/            # TypeScript type definitions
│       ├── agent.ts
│       ├── agui.ts
│       └── chat.ts
│
└── agents.md             # Development guidelines
```

## 🔌 API Reference

### Backend Endpoints

#### POST /api/chat
Chat with the agent using AG-UI protocol.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, how can you help me?"}
  ]
}
```

**Response:** Server-Sent Events (SSE) stream with AG-UI events:
- `RUN_STARTED`: Agent execution begins
- `TEXT_MESSAGE_CHUNK`: Streaming text response
- `RUN_FINISHED`: Agent execution complete
- `ERROR`: Error occurred during execution

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"messages":[{"role":"user","content":"Hello!"}]}'
```

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## 🧩 Key Components

### Backend

- **BaseAgent**: Abstract base class for agents with AG-UI event emission
- **ChatAgent**: Main conversational agent implementation
- **ChatGraph**: LangGraph workflow for chat orchestration
- **LLMProviderFactory**: Factory for creating LLM provider instances
- **AG-UI Event Encoder**: Custom JSON encoder for AG-UI events

### Frontend

- **useAGUI**: React hook for AG-UI event stream handling
- **useChatThreads**: Hook for thread management
- **useMessages**: Hook for message state management
- **ChatContainer**: Main chat interface component
- **MessageBubble**: Individual message display component
- **AG-UI Client**: Service for SSE connection management

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# LLM Provider Settings
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b

# Optional: LangFuse Observability
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🧪 Development

### Adding New Agents

1. Create a new agent class in `backend/agents/` inheriting from `BaseAgent`
2. Implement the `_execute()` method with your agent logic
3. Emit AG-UI events for frontend visibility
4. Register the agent in the LangGraph workflow

Example:
```python
from agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    async def _execute(self, state: dict) -> dict:
        await self.emit_thinking("Processing your request...")
        
        # Your agent logic here
        result = await self.process(state)
        
        await self.emit_complete("Task completed!")
        return {"result": result}
```

### Adding New UI Components

1. Create component in `frontend/components/`
2. Use Shadcn UI primitives from `components/ui/`
3. Integrate with AG-UI hooks for real-time updates
4. Add TypeScript types in `types/`

### Testing

**Backend:**
```bash
cd backend
pytest tests/
```

**Frontend:**
```bash
cd frontend
npm test
```

## 📚 Documentation

Detailed documentation available in the `.docs/` directory:

- **Implementation Plans**: `.docs/1-implementation-plans/`
- **Knowledge Base**: `.docs/2-knowledge-base/`
- **Backend Guide**: [backend/README.md](backend/README.md)
- **Frontend Guide**: [frontend/README.md](frontend/README.md)
- **Development Guidelines**: [agents.md](agents.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **LangGraph** for multi-agent orchestration
- **AG-UI Protocol** for agent-frontend communication
- **Shadcn UI** for beautiful UI components
- **Ollama** for local LLM inference
- **FastAPI** for the robust backend framework
- **NextJS** for the modern frontend framework

## 🐛 Troubleshooting

### Backend Issues

**Ollama connection fails:**
```bash
# Ensure Ollama is running
ollama serve

# Verify model is available
ollama list
ollama pull qwen:7b
```

**Port 8000 already in use:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

### Frontend Issues

**API connection fails:**
- Verify backend is running on `http://localhost:8000`
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Check CORS settings in backend

**Build errors:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `.docs/`
- Review [agents.md](agents.md) for development patterns

---

Built with ❤️ using LangGraph, AG-UI, FastAPI, and NextJS
