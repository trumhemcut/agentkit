# AgentKit

**Modern multi-agent AI assistant with LangGraph & AG-UI**

> 🌐 [Tiếng Việt](README_VI.md) | **English**

Build powerful AI applications with real-time streaming, interactive UI components, and multi-agent orchestration.

![AgentKit Chat Interface](chat_screen.png)

## ✨ Features

- **🎛️ A2UI Protocol**: Agents generate interactive UI components (checkboxes, forms, buttons) in chat
- **🎨 Canvas Mode**: Full-screen workspace for complex agent workflows
- **🔄 Multi-Agent Orchestration**: LangGraph-powered workflow management
- **⚡ Real-time Streaming**: AG-UI protocol with instant agent feedback
- **💬 Thread Management**: Persistent conversation threads with SQLite/PostgreSQL
- **🎯 Modern Stack**: NextJS + Shadcn UI + FastAPI + LangGraph
- **🔌 Multi-LLM Support**: Ollama, Azure OpenAI, Gemini, and more
- **🛡️ Type-Safe**: TypeScript frontend, Python type hints backend
- **📊 Observability**: Optional LangFuse integration

## 🚀 Getting Started

### Prerequisites

1. **Python 3.10+** and **Node.js 18+**
2. **Ollama** (or configure Azure OpenAI/Gemini):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull qwen:7b
   ```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env for Azure OpenAI, Gemini, or PostgreSQL

# Run database migrations
python migrate.py

# Start server
python main.py
```

✅ Backend running at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ Frontend running at `http://localhost:3000`

## 🗄️ Database Configuration

**SQLite** (default - zero config):
```bash
DATABASE_URL=sqlite+aiosqlite:///./agentkit.db
```

**PostgreSQL** (production):
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agentkit
```

Run migrations after any config change:
```bash
python migrate.py
```

## 🔌 LLM Provider Configuration

Edit `.env` in backend directory:

**Ollama** (default):
```bash
DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

**Azure OpenAI**:
```bash
DEFAULT_PROVIDER=azure-openai
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
```

**Gemini**:
```bash
DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │◄────────│   AG-UI      │────────►│   Backend   │
│  (NextJS)   │  SSE    │   Protocol   │  HTTP   │  (FastAPI)  │
└─────────────┘         └──────────────┘         └─────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │  LangGraph  │
                                                   │   Agents    │
                                                   └─────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │  LLM Provider│
                                                   │  (Ollama/   │
                                                   │   Azure/    │
                                                   │   Gemini)   │
                                                   └─────────────┘
```

**Backend Stack**:
- FastAPI + LangGraph + AG-UI Protocol
- SQLAlchemy (async) + SQLite/PostgreSQL
- Ollama/Azure OpenAI/Gemini

**Frontend Stack**:
- NextJS 14 + TypeScript + Shadcn UI
- AG-UI client for event streams
- LocalStorage for thread persistence

## 📚 Documentation

- [Multi-Agent Architecture](agents.md)
- [Database Setup](backend/DATABASE.md)
- [A2UI Protocol](backend/A2UI_README.md)
- [Canvas Mode](backend/CANVAS_README.md)
- [Implementation Plans](.docs/1-implementation-plans/)
- [Knowledge Base](.docs/2-knowledge-base/)

## 🛠️ Development

### Project Structure

```
agentkit/
├── backend/              # FastAPI + LangGraph backend
│   ├── agents/          # Agent implementations
│   ├── graphs/          # LangGraph workflows
│   ├── api/             # REST endpoints
│   ├── database/        # SQLAlchemy models & migrations
│   ├── llm/             # LLM provider integrations
│   ├── protocols/       # AG-UI protocol implementation
│   └── main.py          # Entry point
├── frontend/            # NextJS frontend
│   ├── app/            # App router pages
│   ├── components/     # React components
│   ├── services/       # API client
│   └── types/          # TypeScript types
└── .docs/              # Documentation
```

### API Endpoints

**Chat**: `POST /api/chat` - Stream agent responses
**Threads**: `GET/POST /api/threads` - Manage conversations
**Messages**: `GET /api/threads/{id}/messages` - Get thread history
**Health**: `GET /health` - Server status

### Adding New Agents

1. Create agent in `backend/agents/`
2. Define graph in `backend/graphs/`
3. Register in `backend/agents/agent_registry.py`
4. Update frontend components if needed

See [agents.md](agents.md) for detailed guide.

## 🧪 Testing

**Backend**:
```bash
cd backend
pytest
```

**Frontend**:
```bash
cd frontend
npm test
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

## 🌟 Show Your Support

If you find AgentKit useful, please consider giving it a star ⭐️
